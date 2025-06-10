def cli_loop(handle, whoisport):
    known_users = {}
    print("Verfügbar: who, users, send, quit, name")


    while True:
        try:
            command = input("Command > ").strip()

            if command == "who":
                print("")

            elif command == "users":
                print("")
            elif command.startswith("send"):
                print("")

            elif command.startswith("img:"):
                print("")

            elif command == "quit":
                print("")
            elif command == "name":
                print("")

            
            else:
                print("Unbekannter Befehl. Verfügbare: who, users, send, quit")

        except KeyboardInterrupt:
            send_leave(handle,whoisport)
            print("\n[Client] Abbruch mit Strg+C. LEAVE gesendet.")
            break