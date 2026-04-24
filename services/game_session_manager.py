import time
import uuid
from datetime import datetime

from models.game_session import (
    GameRecord,
    GamingSession,
    PauseRecord,
    SessionEndReason,
    SessionParameters,
    SessionStatus,
)
from utils.validator import validate_bets, validate_boundaries, validate_positive_amount, validate_probability


class GameSessionManager:
    def __init__(self, betting_service, stake_service):
        self.betting_service = betting_service
        self.stake_service = stake_service
        self._sessions = {}
        self._active_by_gambler = {}

    def start_new_session(
        self,
        gambler_id,
        lower_limit,
        upper_limit,
        min_bet,
        max_bet,
        max_games,
        max_duration_seconds,
        default_win_probability,
    ):
        if gambler_id in self._active_by_gambler:
            raise ValueError("Gambler already has an active/paused session")

        validate_boundaries(lower_limit, upper_limit)
        validate_bets(min_bet, max_bet)
        validate_positive_amount(max_games, "max_games")
        validate_positive_amount(max_duration_seconds, "max_duration_seconds")
        validate_probability(default_win_probability)

        stake = self.stake_service.track_current_stake(gambler_id)["current_stake"]
        if not (lower_limit < stake < upper_limit):
            raise ValueError("Current stake must be between lower and upper limits")

        params = SessionParameters(
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            min_bet=min_bet,
            max_bet=max_bet,
            max_games=int(max_games),
            max_duration_seconds=int(max_duration_seconds),
            default_win_probability=default_win_probability,
        )

        session_id = str(uuid.uuid4())
        session = GamingSession(
            session_id=session_id,
            gambler_id=gambler_id,
            parameters=params,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow(),
        )
        self._sessions[session_id] = session
        self._active_by_gambler[gambler_id] = session_id
        return session.to_dict()

    def continue_session(self, session_id, rounds, bet_amount=None, win_probability=None, odds_multiplier=None):
        session = self._get_session(session_id)
        if session.status != SessionStatus.ACTIVE:
            raise ValueError("Session must be ACTIVE to continue")

        rounds = int(rounds)
        validate_positive_amount(rounds, "rounds")

        placed = []
        for _ in range(rounds):
            if self._is_timed_out(session):
                self._end_internal(session, SessionEndReason.TIMEOUT)
                break

            if len(session.games) >= session.parameters.max_games:
                self._end_internal(session, SessionEndReason.MAX_GAMES_REACHED)
                break

            current_stake = self.stake_service.track_current_stake(session.gambler_id)["current_stake"]
            if current_stake >= session.parameters.upper_limit:
                self._end_internal(session, SessionEndReason.UPPER_LIMIT_REACHED)
                break
            if current_stake <= session.parameters.lower_limit:
                self._end_internal(session, SessionEndReason.LOWER_LIMIT_REACHED)
                break

            amount = bet_amount if bet_amount is not None else session.parameters.min_bet
            amount = float(amount)
            if amount < session.parameters.min_bet or amount > session.parameters.max_bet:
                raise ValueError("Bet amount must be within session min/max bet")

            probability = (
                win_probability
                if win_probability is not None
                else session.parameters.default_win_probability
            )
            validate_probability(probability)

            started = time.perf_counter()
            result = self.betting_service.place_bet(
                gambler_id=session.gambler_id,
                amount=amount,
                win_probability=probability,
                odds_multiplier=odds_multiplier,
                strategy_name="game_session",
                session_id=None,
            )
            ended = time.perf_counter()

            bet = result["bet"]
            record = GameRecord(
                game_no=len(session.games) + 1,
                bet_id=bet["bet_id"],
                bet_amount=bet["amount"],
                is_win=bet["is_win"],
                stake_before=bet["stake_before"],
                stake_after=bet["stake_after"],
                duration_seconds=(ended - started),
                played_at=datetime.utcnow(),
            )
            session.games.append(record)
            if record.is_win:
                session.wins += 1
            else:
                session.losses += 1
            session.total_profit += (record.stake_after - record.stake_before)
            placed.append(record.to_dict())

            if record.stake_after >= session.parameters.upper_limit:
                self._end_internal(session, SessionEndReason.UPPER_LIMIT_REACHED)
                break
            if record.stake_after <= session.parameters.lower_limit:
                self._end_internal(session, SessionEndReason.LOWER_LIMIT_REACHED)
                break

        return {
            "session": session.to_dict(),
            "new_games": placed,
        }

    def pause_session(self, session_id, reason="User requested pause"):
        session = self._get_session(session_id)
        if session.status != SessionStatus.ACTIVE:
            raise ValueError("Session must be ACTIVE to pause")

        session.status = SessionStatus.PAUSED
        session.pauses.append(PauseRecord(paused_at=datetime.utcnow(), reason=reason))
        return session.to_dict()

    def resume_session(self, session_id):
        session = self._get_session(session_id)
        if session.status != SessionStatus.PAUSED:
            raise ValueError("Session must be PAUSED to resume")

        if session.pauses and session.pauses[-1].resumed_at is None:
            resumed = datetime.utcnow()
            session.pauses[-1].resumed_at = resumed
            session.pauses[-1].duration_seconds = (
                resumed - session.pauses[-1].paused_at
            ).total_seconds()
            session.total_paused_seconds += session.pauses[-1].duration_seconds

        session.status = SessionStatus.ACTIVE
        return session.to_dict()

    def end_session(self, session_id, reason=SessionEndReason.MANUAL):
        session = self._get_session(session_id)
        return self._end_internal(session, reason)

    def get_session(self, session_id):
        session = self._get_session(session_id)
        return session.to_dict()

    def list_active_sessions(self):
        return [
            self._sessions[sid].to_dict()
            for sid in self._active_by_gambler.values()
            if sid in self._sessions
        ]

    def _end_internal(self, session, reason):
        if session.status in {
            SessionStatus.ENDED_WIN,
            SessionStatus.ENDED_LOSS,
            SessionStatus.ENDED_MANUAL,
            SessionStatus.ENDED_TIMEOUT,
            SessionStatus.ENDED_MAX_GAMES,
        }:
            return session.to_dict()

        if session.status == SessionStatus.PAUSED and session.pauses and session.pauses[-1].resumed_at is None:
            resumed = datetime.utcnow()
            session.pauses[-1].resumed_at = resumed
            session.pauses[-1].duration_seconds = (
                resumed - session.pauses[-1].paused_at
            ).total_seconds()
            session.total_paused_seconds += session.pauses[-1].duration_seconds

        session.end_reason = reason
        session.ended_at = datetime.utcnow()

        status_map = {
            SessionEndReason.UPPER_LIMIT_REACHED: SessionStatus.ENDED_WIN,
            SessionEndReason.LOWER_LIMIT_REACHED: SessionStatus.ENDED_LOSS,
            SessionEndReason.MANUAL: SessionStatus.ENDED_MANUAL,
            SessionEndReason.TIMEOUT: SessionStatus.ENDED_TIMEOUT,
            SessionEndReason.MAX_GAMES_REACHED: SessionStatus.ENDED_MAX_GAMES,
        }
        session.status = status_map[reason]

        if session.gambler_id in self._active_by_gambler:
            del self._active_by_gambler[session.gambler_id]
        return session.to_dict()

    def _is_timed_out(self, session):
        return session.active_duration_seconds() >= session.parameters.max_duration_seconds

    def _get_session(self, session_id):
        if session_id not in self._sessions:
            raise ValueError("Session not found")
        return self._sessions[session_id]
