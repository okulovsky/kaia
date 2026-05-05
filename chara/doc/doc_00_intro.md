# `chara`

Chara is a collection of research scripts that are primarly used to create characters.

Currently, two branches are covered:
* Paraphrasing. This is used to paraphrase the outputs of Kaia so that they match to the personality of the character.
The pipeline will take the replies from the assistant, take the previously generated paraphrases from Avatar server,
determine which replies need more coverage, paraphrase them and upload the results back to the Avatar server.
All you need to do is to define the characters and their personalities.
Under the hood, this system generate the paraphrases for arbitrary `grammatron` Templates,
which can be used elsewhere: e.g. we also use it in natural-language understanding research.
* Voice cloning will help you to create character's voices. It will take the voice sample of your character,
then the GPU-requiring zero-shot voice cloner generate an hours-long dataset of phrases,
and then the lightweight Piper model will be trained on this dataset.

Both systems support different languages. Currently German, English and Russian are implemented,
others can be added with some additional effort.

For the detailed description of these project, please consult the README.md files in the respective directories.

## General concepts

`chara` infrastructure offers a way to write the reproducible, maintainable and deliverable research.
Traditionally, the research is often done in notebooks, and while they are very handy for research,
they are also terrible in production. It's hard to pass the parameters to the notebook, or to write a unit tests for it,
or to call one notebook from another, etc. Hence, the code is often rewritten as a pure Python,
but then it loses the benefits of the notebooks: visualizations that may still be useful in production for the
quality control. Also, after the conversions, the intermediate values are no longer cached in memory, and
so if your several hours long pipeline gives incorrect result in the end, it's not possible no understand why.
Also, it's impossible to fix the bug and restart the pipeline from the partially computed state.

I've been suffering from these problems for quite awhile, and `chara` became a simple and efficient solution.
First, `foundation_kaia.logger` provides a logger that can consume plots, dataframes and ipynotebook widgets
and output them to the HTML files. This way you can still enjoy your intermediate visualizations,
copied straight from notebooks.

Second, `chara` offers the caching infrastruture, seamlessly build over the functions call.

### Caching

If you need to cache the results of the `function(*args, **kwargs)`, just write `Chara.start(folder)`, and then
`Chara.call(function)(*args, **kwargs)`. This will cache the returned value of `function` in the folder,
so if the `function` is called again, the value will be restored and `function` won't be called again.
If `function` calls other functions inside with `Chara.call`, the subfolders with the interpretable names
will be created to cache the results of the internal calls. In case something went wrong,
you can invalidate the cache: `invalidate_self(path)` will invalidate the result of the function's call,
but not the results of the inner calls, while `invalidate_down` will reset the associated cache completely.
Also, these functions remove the caches of all the functions called after the desired path, and
remove the cached results of all the function up on the stack, so basically this corresponds to
"repeat the pipeline from the selected place".

Obviously, caches need a bit of architectural redesign of the code, e.g.
1) If the code is called with the different parameters, the `folder` needs to be changed or reseted
2) The code shouldn't have branching on the `Chara.call` calls. If you need to conditionally run the function,
call it anyway and return None.

In addition, you may use the `Chara.phase` decorator to subdivide a function without extracting functions from them:

```
def function(argument):

  @Chara.phase
  def first_formula():
    return argument + 1

  first_result = Chara.last.result

  @Chara.phase
  def second_formula():
    return first_result * 2

  second_result = Chara.last.result
  return 1 / second_result
```

This will create two caches, for the `first_formula` and the `second_formula`, and store the intermediate values there.

Finally, all the functions can get the access to the current folder with `Chara.current`. That allows to store
some additional files there. Since `chara` pipelines work with media, they are quite heavy on files, and this
functionality is very handy.

## Integrations

There are some important integrations that offer you the basic building blocks for your pipelines.
The most important ones are BrainBox integrations. `brainbox_training_pipeline` runs
the training process (such as e.g. `PiperTraining.train`), monitors the progress and interprets the results.
`brainbox_pipeline` accepts the Iterable of tasks, adds them to the server, and then stores the pickled results
in the `tar` file, without placing it in the memory at once. If the result of the task is file or several files,
the pipeline downloads these files from the server, and in this case the paths of the downloaded files
will be stored in the `tar` file. This `tar` file can then be iteratively read, again, without placing
its content in the memory at once.

## Cases

Most of the integrations implement the pattern of `ICasePipeline`: they accept the list of __cases__ (essentially, arbitrary dataclasses),
modify the cases (or replace with other cases), and return the updated collection or the same one.
This is extremely convenient when you need e.g. to run several BrainBox tasks that are associated with, e.g. a particular file,
and then bring together the results. `BrainBoxCasePipeline` does just this: builds a task for each case,
and then places the result of the task to the case's field.

`AnnotationPipeline` is also very useful. When working with GenAI, it is often needed to annotate data,
e.g. rejecting some of the data points by quality. `AnnotationPipeline` accepts the list of the cases,
displays each case and collects the feedback. Display is done via `IAnnotator`, and right now a Gradio-based
`GradioLabelAnnotator` is available.

There are also collective actions on the cases. Such pipelines accept `inner_pipeline: ICasePipeline`, and:
* `RepeatUntilDonePipeline` calls `inner_pipeline` several times on the array of the cases, excluding those cases that received a non-erroneous answer.
* `ChooseBestAnswerPipeline` calls `inner_pipeline` several times on all cases, then select the most popular answer. This is handy if you need the LLMs to vote on the result.
* `BatchingPipeline` selects several cases from the bigger subset and calls the `inner_pipeline` on them, thus providing the manageable execution time of each batch and control over when to stop the process.

