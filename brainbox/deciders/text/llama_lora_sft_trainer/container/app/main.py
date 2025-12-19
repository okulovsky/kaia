import argparse
from trainer import Trainer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--exp-folder",
        type=str,
        required=True,
        help="Relative path to the experiment folder (adapter_name/guid)",
    )

    args = parser.parse_args()
    print(f"Training in {args.exp_folder}")

    trainer = Trainer(args.exp_folder)

    print("Training settings:")
    print(trainer.settings)

    print("TRAINING")
    trainer.train()

    print("CONVERTING LORA TO GGUF")
    trainer.convert_lora_to_gguf()
