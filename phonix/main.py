import argparse
import threading

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', required=True, help="IP address of the Avatar server (e.g. 127.0.0.1)")
    parser.add_argument('-p', '--port', required=True, help="Port of the Avatar server at the specified IP address")
    parser.add_argument('-s', '--silence-level', required=True, help="The sound level which is considered silence. Must be picked for each mic experimentally!")
    parser.add_argument('-l', '--silence-margin-length', default="1.0", help="The required period of silence after wakeword and after sound command")
    parser.add_argument('-q', '--quiet', default='False', help="If True, will show the current state and mic level in the console")
    parser.add_argument('-t', '--tolerate-errors', default='True', help="If True, will try to continue after exceptions indefinitely (production mode)")
    parser.add_argument('-a', '--async-messaging', default='True', help="If True, messaging processing is decoupled from ")
    parser.add_argument('-o', '--output-backend', default='PyAudio', help='Backends for the output: PyAudio or Sox')
    parser.add_argument('-r', '--report-volume', default='', help='Rate in seconds between volume checks')
    parser.add_argument('-n', '--new-porcupine-config', default='', help='Config, if new porpucine is required')

    args = parser.parse_args()

    print("Initializing the daemon")
    print(args)
    from phonix.app import PhonixAppSettings
    settings = PhonixAppSettings(
        float(args.silence_level),
        args.ip,
        int(args.port),
        float(args.silence_margin_length),
        bool(args.quiet),
        bool(args.tolerate_errors),
        bool(args.async_messaging),
        args.output_backend,
        args.new_porcupine_config
    )
    daemon = settings.create_daemon()


    if args.report_volume != '':
        from phonix.daemon import VolumeDeamon
        volume_rate = float(args.report_volume)
        volume_daemon = VolumeDeamon(daemon.base_client, daemon.volume_controller, volume_rate)
        thread = threading.Thread(target=volume_daemon.run, daemon=True)
        thread.start()




    print("Starting the deamon")
    daemon.run()
