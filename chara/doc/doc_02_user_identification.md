# `user_identification`

Both voice- and face recognition work with the same pipeline:
* Brainbox service converts a media file to vector (Resemblyzer for voice and InsightFace for face)
* Respective Avatar service (SpeakerIdentificationService for voice and UserWalkIn for face) store the set of the 
images/sounds, associated with users, and computed vectors. When the new image/sound arrive, 
the `VectorIdentifier` instance finds the nearest neighbors to the vector and hence the winner.
* That means "training" in this case actually means "annotating": you need to review a certain amount of samples and assign user to each of them.

Pipelines `VoiceIdentification` and `FaceIdentification` have the same functionality, 
they are only different in terms where do they take data from, which vectorizer they apply 
and where the result is stored.

`annotation` method will first download the files from Avatar's cache to you local
machine, and from there to the local BrainBox (the assumption is that you're going
to use a different BrainBox instance for the research, not the one supporting inference
on you server). Then, it will run Gradio annotator. The annotator tries to be 
smart, and employ different strategies depending on the state of the annotation:
random at first, balancing the sets if they very be size too much, or fine-tunning borders.

`refinement` method re-annotates currently used dataset. Sometimes Kaia make mistakes by identification,
and you have the opportunity to correct it, which also stores sample in the service's resources.
But sometimes you make mistake when correcting it, and `refinement` pipeline will help you with this.

