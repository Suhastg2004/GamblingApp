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
            print("6. Exit")

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
    initialize()   # ensures DB + tables exist
    run_app()      # runs UC1