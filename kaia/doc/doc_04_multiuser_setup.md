# Kaia in a household with multiple users

Kaia can detect a user by voice and by face, but you need to show the algorithm, "who is who".

To do that, let Kaia work for some time as is. Even though Kaia won't use the data 
for identification, it will still collect the data, so after a couple of days 
you will have your own media dataset.

Define the names of the users who live in the household. 

Then, using these names, annotate the dataset with `chara.user_identification` pipelines.

In `avatar_daemon_app_settings.py`, add these methods:

```
def create_speaker_identification_service(self, app: KaiaApp, state: s.State):
    return SpeakerIdentificationService(
        app.avatar_api,
        BestOfStrategy(10),
    )

def create_face_identification_service(self, app: KaiaApp, state: s.State):
    return UserWalkInService(
        app.avatar_api,
        BestOfStrategy(10),
    )
```

This will add the services to the Avatar middleware. 

Then, in `kaia_driver_settings.py`, add this skill to the list of skills:

```
self.skills.append(skills.RecognitionFeedbackSkill(user_names))
```

where users are the names of the people living in the household.
This will allow you to correct Kaia's identification: if you see that 
the identification failed, you can say "I'm actually <your_name>",
and the identification dataset will be expanded by an erroneous sample (with the proper annotation).

In `avatar_daemon_app_settings.py` you can also make use of `_speaker_to_image_url`:
place the avatars of your household's members to the `kaia/web/static` folder,
and map username to the avatar's path.

Finally, you can now use `UserWalkInSkill`. Define an array `announcements` of `WalkInAnnouncement` objects,
and then `self.skills.append(skills.WalkInSkill(announcements))`. When Kaia sees you, you will
receive the announcement according to the schedule.

