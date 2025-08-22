import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', required=True, help="IP address of the Avatar server (e.g. 127.0.0.1)")
    parser.add_argument('-p', '--port', required=True, help="Port of the Avatar server at the specified IP address")
    parser.add_argument('-s', '--silence-level', required=True, help="The sound level which is considered silence. Must be picked for each mic experimentally!")
    parser.add_argument('-l', '--silence-margin-length', default="1.0", help="The required period of silence after wakeword and after sound command")
    parser.add_argument('-q', '--quiet', default='False', help="If True, will show the current state and mic level in the console")
    parser.add_argument('-t', '--tolerate-errors', default='True', help="If True, will try to continue after exceptions indefinitely (production mode)")
    parser.add_argument('-a', '--async-messaging', default='True', help="If True, messaging processing is decoupled from ")

    args = parser.parse_args()

    print("Initializing the daemon")
    from phonix.app import PhonixAppSettings
    settings = PhonixAppSettings(
        float(args.silence_level),
        args.ip,
        int(args.port),
        float(args.silence_margin_length),
        bool(args.quiet),
        bool(args.tolerate_errors)
    )
    daemon = settings.create_daemon()

    print("Starting the deamon")
    daemon.run()
