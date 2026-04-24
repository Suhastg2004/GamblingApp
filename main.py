from config.init_db import create_database, create_tables
from services.gambler_profile_service import GamblerProfileService
from utils.logger import logger

def initialize():
    try:
        print("Initializing database...")
        create_database()
        create_tables()
        print("Database ready.\n")
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"DB Initialization failed: {e}")
        print("Database setup failed. Check logs.")
        exit()

def run_app():
    service = GamblerProfileService()

    while True:
        try:
            print("\n===== GAMBLER PROFILE MANAGEMENT =====")
            print("1. Create Gambler")
            print("2. Get Gambler Details")
            print("3. Update Gambler")
            print("4. Validate Gambler")
            print("5. Reset Gambler")
            print("6. Track Current Stake")
            print("7. Process Bet Outcome")
            print("8. Deposit Funds")
            print("9. Withdraw Funds")
            print("10. Stake Fluctuation Monitor")
            print("11. Validate Stake Boundaries")
            print("12. Stake History Report")
            print("13. Exit")

            ch = input("Enter choice: ").strip()

            if ch == "1":
                name = input("Enter name: ")
                initial_stake = float(input("Enter initial stake: "))
                win_th = float(input("Enter win threshold: "))
                loss_th = float(input("Enter loss threshold: "))
                min_bet = float(input("Enter min bet: "))
                max_bet = float(input("Enter max bet: "))
                strategy = input("Enter strategy: ")
                session_limit = int(input("Enter session limit: "))

                gid = service.create_gambler(
                    name, initial_stake, win_th, loss_th,
                    min_bet, max_bet, strategy, session_limit
                )

                print(f"Gambler created with ID: {gid}")

            elif ch == "2":
                gid = int(input("Enter gambler ID: "))
                data = service.get_gambler(gid)

                if not data["profile"]:
                    print("Gambler not found")
                else:
                    print("\n--- Profile ---")
                    print(data["profile"])
                    print("\n--- Preferences ---")
                    print(data["preferences"])
                    print("\n--- Statistics ---")
                    print(data["statistics"])

            elif ch == "3":
                gid = int(input("Enter gambler ID: "))
                name = input("Enter new name (leave blank to skip): ").strip()
                win_th = input("Enter new win threshold (blank to skip): ").strip()
                loss_th = input("Enter new loss threshold (blank to skip): ").strip()

                name = name if name else None
                win_th = float(win_th) if win_th else None
                loss_th = float(loss_th) if loss_th else None

                service.update_gambler(gid, name, win_th, loss_th)
                print("Gambler updated successfully")

            elif ch == "4":
                gid = int(input("Enter gambler ID: "))
                valid = service.validate_gambler(gid)

                print("Eligible" if valid else "Not Eligible")

            elif ch == "5":
                gid = int(input("Enter gambler ID: "))
                service.reset_gambler(gid)
                print("Gambler reset successfully")

            elif ch == "6":
                gid = int(input("Enter gambler ID: "))
                status = service.get_stake_status(gid)
                print("\n--- Stake Status ---")
                print(status)

            elif ch == "7":
                gid = int(input("Enter gambler ID: "))
                amount = float(input("Enter bet amount: "))
                is_win_input = input("Did gambler win? (y/n): ").strip().lower()
                is_win = is_win_input == "y"
                payout_multiplier = float(input("Enter payout multiplier (default 2.0): ") or "2.0")
                bet_id = input("Enter bet id (optional): ").strip() or None
                result = service.process_bet(gid, amount, is_win, payout_multiplier, bet_id)
                print("\n--- Bet Result ---")
                print(result)

            elif ch == "8":
                gid = int(input("Enter gambler ID: "))
                amount = float(input("Enter deposit amount: "))
                note = input("Enter note (optional): ").strip() or None
                result = service.deposit(gid, amount, note)
                print("\n--- Deposit Result ---")
                print(result)

            elif ch == "9":
                gid = int(input("Enter gambler ID: "))
                amount = float(input("Enter withdrawal amount: "))
                note = input("Enter note (optional): ").strip() or None
                result = service.withdraw(gid, amount, note)
                print("\n--- Withdrawal Result ---")
                print(result)

            elif ch == "10":
                gid = int(input("Enter gambler ID: "))
                monitor = service.get_stake_monitor(gid)
                print("\n--- Stake Monitor ---")
                print(monitor)

            elif ch == "11":
                gid = int(input("Enter gambler ID: "))
                result = service.validate_stake_boundaries(gid)
                print("\n--- Boundary Validation ---")
                print(result)

            elif ch == "12":
                gid = int(input("Enter gambler ID: "))
                tx_type = input("Filter by transaction type (optional): ").strip() or None
                limit = int(input("Enter report row limit (default 200): ") or "200")
                report = service.get_stake_history_report(gid, tx_type, limit)
                print("\n--- Stake History Report ---")
                print(report)

            elif ch == "13":
                print("Exiting application...")
                break

            else:
                print("Invalid choice")

        except ValueError as ve:
            logger.warning(f"Invalid input: {ve}")
            print("Invalid input. Please enter correct values.")

        except Exception as e:
            logger.error(f"Application error: {e}")
            print("Something went wrong. Check logs.")

if __name__ == "__main__":
    initialize()  # ensures DB + tables exist
    run_app()  # runs UC1 + UC2