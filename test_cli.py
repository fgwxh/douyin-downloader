from src.scheduler import Scheduler

if __name__ == '__main__':
    print("Testing command line functionality...")
    print("This will show the interactive menu. Press 'q' to quit.")
    print("=" * 50)
    scheduler = Scheduler()
    # Print some debug information
    print(f"Settings loaded: {scheduler.settings}")
    print(f"Number of accounts: {len(scheduler.settings.accounts)}")
    print(f"Cookie loaded: {scheduler.cookie}")
    print("=" * 50)
    # Run in interactive mode
    scheduler.run()