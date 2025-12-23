import argparse
from trainer import Trainer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--model-id",
        type=str,
        required=True,
        help="ID of the model being trained",
    )
    parser.add_argument(
        "-a",
        "--adapter-name",
        type=str,
        required=True,
        help="Name of the adapter being trained",
    )
    parser.add_argument(
        "-g",
        "--guid",
        type=str,
        required=True,
        help="GUID of the training run",
    )

    args = parser.parse_args()
    print(f"Training in ../experiments/{args.adapter_name}/{args.guid}")

    trainer = Trainer(args.model_id, args.adapter_name, args.guid)

    print("Training settings:")
    print(trainer.settings)

    print("TRAINING")
    trainer.train()

    print("CONVERTING LORA TO GGUF")
    trainer.convert_lora_to_gguf()
