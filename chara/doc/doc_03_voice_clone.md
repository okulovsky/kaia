# Voice Cloning

Voice Cloning is used to give your character a local and low-compute voice.
There are many cloud services that perform the voiceover, 
but they are paid and often restricted. 

In `voice_clone.common`, several local systems are integrated as Chara pipelines.
These integrations address peculiarities in the systems' requirements 
to the training data or inference parameters.
For quite a while, the local voice cloners couldn't match the cloud services
in terms of quality or language coverage, but CosyVoice closes this gap,
producing excellent voiceovers in many common languages.

However, running CosyVoice requires GPU, and this is not what we aim for the assistant.
We need a lighter model, Piper, that can run on the CPU and on Raspberry Pi,
but cannot do zero-shot voice cloning: instead, it needs to be properly fine-tuned
on 1+ hours of data for each character. So we create this dataset with CosyVoice,
and then train Piper.

`voice_clone.dataset` produces the __text__ dataset, that is later voiced over by CosyVoice.
This step is needed, because the voiceovers need to represent all the phonemes of target
language, ever rare ones. The algorithm is employed to select the sentences so
that all the phonemes are well-represented. Also, it's important that no
foreign words were added to this dataset, because e.g. for German CosyVoice
tends to pronounce anglicisms in pure English, not in German, thus reducing the quality.
This is why the sentences also need an additional review.

`voice_clone.upsampling` creates the voice dataset:
* It adds prefixes and suffixes to each line of the text dataset 
(many systems, including CosyVoice, tend to stutter or produce noises at the beginning and the end of the text, 
so the prefixes and suffixes are buffers for this stutter, and will be later removed)
* Voices over the modified line
* Converts the voiceover back to text with VOSK to:
  * detect the cases that are voiced over plainly wrong (sometimes CosyVoice produces the voiceovers that have nothing to do with the text)
  * detect the usable part of the voiceover without suffix and prefix
* Then, the files are exported to the archive in the format that is needed by PiperTraining.

`voice_clone.training` runs the training, and obtains several checkpoints. 
Then, the evaluation procedure uploads each of these checkpoints to Piper,
voices over a boilerplate text, and outputs the results in the HTML format.
You can check this file and select the checkpoint you like most, or increase/reduce the amount of epochs required.
After achieving a good quality, the model may be uploaded to Piper again, manually, with the proper name of the character.
Then, `kaia.app.avatar_daemon_settings` may finally be changed to set the list of the characters to yours, and map the models' names to the characters.

