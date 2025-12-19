# Dataset for SFT LoRA Training

The adapter will learn to generate the `OUTPUT` string given an `INPUT` string. 
Each training sample consists of an `INPUT` and an `OUTPUT` field.

## File Format

* **File extension:** `.jsonl` (JSON Lines)
* **Each line** in the file corresponds to a single training example.
* **Fields per sample:**

  * `INPUT` – the input string that the model receives
  * `OUTPUT` – the target output string that the model should generate

Example of a single line in the dataset:

```json
{"INPUT": "USER:set a timer for 3 hours\n", "OUTPUT": "HOURS:3\nMINUTES:0\nSECONDS:0"}
```

### Notes

* Using JSON format for the OUTPUT field is usually not ideal, because the extra brackets and quotes add unnecessary complexity, extra tokens for the model.

* Instead, consider a simpler format, e.g., using \n to separate fields, as in the example above. You can also choose any other format that is convenient for your task, as long as it’s consistent.
