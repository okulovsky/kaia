# Paraphrases

## `paraphrases.common`

This pipeline paraphrases the `grammatron.Template`, possible also translating it to other languages.

First, templates undergo paraphrasing.

* The input case contains `Template` and covariates that are used in the prompt.
* The template is parsed into one or many `ParsedTemplate`, the case is split if necessary. 
Each `ParsedTemplate` contains all the lines with the same set of variables.
E.g. if the template has lines "Set the timer", "Please create a timer" and "Set the {index} timer", 
there will be two `ParsedTemplates`: one for "Set the timer" and "Please create a timer", and another for "Set the {index} timer".
The order of the variables does not matter.
* The cases are fed to the `TemplateParaphrasing`. For each case, a multiple lines of possible 
variations is given. The case is split again, one case per each variation.

Then, in case it's translation, following steps are needed:
* If the template has options, these options need to be translated
* If the template is translated to German or Russian, the grammatical form needs to be determined for each variable. 
To get basic understanding about grammatical forms, consult `grammatron` documentation.
The grammatic correction essentially asks LLM several times what is the correct casus/article, and 
select the most popular answer. It doesn't work flawlessly though.
* In some use cases, like dataset generation one might need to additionally create more options for the OptionsDub.

These settings can be configured in the Paraphrase.Settings class.

## `paraphrasing.utterances`

This is a production-ready script that is supposed to operate on a live Avatar Server, 
where your Kaia is running, and a BrainBox server (that will probably be a different one from Kaia instance, 
since a good GPU is required for LLMs).

The entry point is UtteranceParaphraseCase that contains:
* a template (they come from KaiaAssistant.get_replies)
* list of `Character` definitions: for each character, you need a name and a short story
* optional list of users, also specified by `Character`.
* dictionary of relationships between characters and users
* `target_language`: `ru`, `de`, or `en`. Right now, Kaia is not ready to fully handle multiple language (the deficit is at NLU part)

After that, create `Paraphrase.Settings`, then `UtteranceParaphrasePipeline`, and run it.

It will connect to the Avatar server and dowload existing paraphrases and their usages statistics.
Then, it will determine which templates are in need of paraphrasing, create the paraphrases
and upload them to server. Reloading of the KAIA GUI interface will trigger the reloading of `ParaphrasingService`
on the server side, and new paraphrases will become available.

`paraphrases_upper_count` parameter manages the paraphrasing: no templates with more paraphrases than this amount will be taken into account.
Set it to 0 if you added some new templates and want only them to be paraphrased. Set them to e.g. 30 to ensure that every template has at least 30 paraphrases.
Without this parameter, the paraphrasing will continue until `max_attemps`, prioritizing the templates that are in the heavy usage.
