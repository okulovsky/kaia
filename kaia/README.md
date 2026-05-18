# Table of contents

* [Running Kaia locally](#running-kaia-locally)
  * [Docker](#docker)
  * [Node.js](#node.js)
  * [Python environment](#python-environment)
  * [Installing and running Kaia](#installing-and-running-kaia)
  * [Deployment](#deployment)
* [Extending functionality](#extending-functionality)
  * [Adding a new skill](#adding-a-new-skill)
* [Kaia in a household with multiple users](#kaia-in-a-household-with-multiple-users)
* [Creating the characters](#creating-the-characters)

# Running Kaia locally

Clone the repository `github.com/okulovsky/kaia` at your local machine.

## Docker

You need [Docker](https://docs.docker.com/engine/install/) installed in your system,
and the access granted to the current user to run `docker` from command line without elevated privileges.
The command

```commandline
docker run hello-world
```

should work successfully and produce the text starting with "Hello from Docker!"

## Node.js

The project has TypeScript source files for frontend, that needs to be compiled. To do so, Node.js must be installed:

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
```

```
source ~/.bashrc
```

```
nvm install --lts
```

Rename `environment.env.example` to `environment.env`. 
Set the variable `NODE_JS_PATH` to the output of `which node` in Linux (`where node` in Windows).
Set the variable `NPM_PATH` to the output of `which npm` (`where npm` in Linux)

## Python environment

[Anaconda](https://www.anaconda.com/download/success) is recommended to manage Python's
environments. Create an environment for e.g. Python 3.12 (BrainBox is tested with 3.10-3.13 Python versions):

```commandline
conda create --name kaia python==3.12
```

Then, activate the environment

```commandline
conda activate kaia
```

## Installing and running Kaia

From the **root directory of the repository** (not from `/kaia` directory), execute:

```
pip install -e .
```

Then, run Kaia by:

```
python -m kaia.run
```

It should produce the following output:

* Lots of lines starting with "Binding": that happens during composing the Kaia application
* "Starting supporting services": that means the four components of the application are starting as subprocesses:
  * `BrainBox` for managing the AI
  * `AvatarServer`, a main application bus
  * `AvatarDaemon`, a middleware that does most of the conversions from the primitives like text into sounds and vice versa
  * `KaiaDriver`, a backend that runs all the skills
* "Starting server on http://127.0.0.1:8090": BrainBox and Avatar web servers are running at the respective addresses.
* "Settings up BrainBox at http://127.0.0.1:8090".
This is where all the AIs, required by Kaia, will be built as containers, self-tested and inistantiated at your machine.
At the very first run, this step will take **a lot** of time and bandwidth.
However, that happens only at the first time you run Kaia.
* Then, the normal process will start and it will be represented by log lines in loguru format.

At this point, the webbrowser will be opened. You should see the loading screen, and then the main interface will appear.
You will need to give the web-page permissions to use the microphone, the web-camera and to play sounds without user's request.

Then, you will need to configure the microphone. Press the cog button in the bottom-left of the screen,
select "MicDebugView", and the following dashboard will appear:

Try speaking to a microphone. You should see the clear spike in the purple bars.
Then, you need to click the buttons on top of the dashboard, adjusting the dashed red line.
When you don't speak, the purple levels should be slightly lower than the line.
When you speak, the levels should be clearly above the line.
The picture shows the correct placement of the line.

Close the panel by clicking the cog button again.

Say "computer". You should hear a beep, that means, the assistant is ready for input.
If you don't hear it, try say it louder and/or clearer, avoiding heavy accent.
After the beep, say "What can you do?". You should hear another beep, and then the computer should respond
with the voice confirmation and the chat message that shows the available commands.





## Deployment

If you wish to use Kaia as a kitchen assistant, the best scenario is to deploy the backend
to the home server ("remote machine"), and then run the frontend on a tablet device ("console").
The deployment is easiest to do with a docker container, and we will
separate this into two parts: BrainBox and everything else. The reason for this split
is that BrainBox is very stable and rarely needs updates, and it's better to leave BrainBox and its child containers
in peace. Avatar and Kaia, however, are areas of the active development, and most of the experiments and improvements
will need these systems redeployed. Therefore, they are bundled into the second container.

To build, deliver and run the containers, I use `brainbox.framework.deployment` subsystem,
the same I use for managing the containers in BrainBox. I admit this choice is questionable
and perhaps more mature dev-ops infrastructure would be an improvement.
With the current solution, however, I'm able to manage the deployment by running exactly one script and zero additional tools,
which makes the onboarding easier for Python developers and especially Data Scientists, who are not always fluent with devops.
Therefore, a mature devops is not my priority, especially given that there is a ton of other, AI-related work to do.

To deploy Kaia, you need to configure the remote and the local machines:
* The remote machine is accessible via SSH without entering the password (e.g. with `ssh-copy-id`)
* Docker is installed on both machines

Start a private Docker registry on the remote machine:

```
docker run -d -p 5000:5000 --restart unless-stopped --name registry registry:2
```

Allow the local machine to push to it: add the remote IP to Docker's insecure registries.
Edit (or create) `/etc/docker/daemon.json` on the local machine:
```json
{ "insecure-registries": ["REMOTE_IP:5000"] }
```
Then restart Docker:
```
sudo systemctl restart docker
```

Сollect the following information from the remote machine and place it in the `environment.env` file:
* username
* user id (`id -u`)
* ip-address
* the folder that will host all data related to Kaia

Run `deploy_brainbox.py`. It will:
* build the container on the local machine
* push it to the private registry on the remote machine (only changed layers are transferred)
* pull and run it on the remote machine

After that, BrainBox should be running at the remote machine on the port `8090`.

I'm not completely sure why, but in this setup it might be the case that BrainBox won't be working
because of the permissions to the `/var/run/docker.sock`. This dirty fix allows to solve this problem:

```
sudo tee /etc/systemd/system/docker-sock-chmod.service <<EOF
[Unit]
Description=Fix docker.sock permissions
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/bin/chmod 666 /var/run/docker.sock

[Install]
WantedBy=multi-user.target
EOF
```

And then:
```
sudo systemctl daemon-reload
sudo systemctl enable docker-sock-chmod.service
```

Then, run `deploy_kaia.py`. After that, the server will be running at `13000` port.

Now the fun starts. Our frontend uses media devices, which means the HTML code must be obtained from trusted source,
thus, localhost or via HTTPS. That means we need to install the HTTPS proxy on the remote machine.

First, install Caddy:

```
sudo apt update

sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl gnupg

curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] \
https://dl.cloudsmith.io/public/caddy/stable/deb/ubuntu any-version main" \
| sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null

sudo apt update

sudo apt install -y caddy
```

Create config file:

```
sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
<ID_ADDRESS_OR_HOST>:13001 {
    tls internal
    reverse_proxy 127.0.0.1:13000
}
EOF
```

Restart Caddy:

```
sudo systemctl restart caddy
```

and export the certificate file:

```
sudo cp /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt ~/caddy-root.crt

sudo chown $USER:$USER ~/caddy-root.crt
```

then, download this file from server and copy to the console.
There, you will need to add this certificate to the browser. We recommend Firefox to run Kaia,
so there it can be done in the menu:

* Settings → Privacy & Security
* Certificates → View Certificates
* Authorities → Import
* Find caddy-root.crt on the console
* Check "Trust this CA to identify websites"

Now, you can open https://[your server ip]:13001 and complete microphone setup.






# Extending functionality

The simplest way to extend the functionality of Kaia is to simply write to the demo folder all the changes you need.
This is perfectly fine if you just want to play with the assistant and learn about its functionality.

However, this approach may expose your code, which may contain the sensitive data, on pushing.
If you do not want it, you may of course simply copy-paste the Kaia code to your repository,
but then you won't be able to update properly.

The correct and private way to do the extension is to install the repository and then create your own
private folder (e.g. in the private repository), that will tweak the `kaia/app` folder.
All classes there are written in such a style that allow easy extension:
e.g., skills are separated into "common skills" like time or date that we assume are helpful for any assistant instance,
and "specific skills" like cookbook, which we encourage the users to setup for their needs.

## Adding a new skill

To add a simple, one-line Kaia skill, where assistant provides an answer to the question, you generally need to:

* Define the template of intent or intents which will trigger the skill
* Define the template of reply to the skill
* Define the logic of the skill.

You can take an inspiration in:
* `PingSkill`: the simplest skill where the intent doesn't have any parameters.
* `DateSkill` or `TimerSkill`: the skill where there are the parameters in the intent
* `EchoSkill`: the simplest skill that demonstrates the free-form input and output, as well as a multi-line skill
* `CookbookSkill` is also a multi-liner, and it shows how to interact with time
* `walk_in_skill` demonstrates how to react not only to spoken commands, but also to the fact that the user become visible to the web cam.

After you've implemented the skill, it is usually a good idea to test it.
The skills are implemented with the `eaglesong` library that offers the convenient way of writing the tests
as the natural dialogs: say this to the assistant, then expect this as a reaction.
`grammatron` library that you will use to define the intents and replies, are designed to be compatible with
`eaglesong` testing procedures. You can, again, take the inspiration in the tests that are provided with the skills.





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





# Creating the characters

For the various reasons we do not provide the library of the characters, nor do we plan it anywhere in the future.
If you want to personalize your assistant, you have to do it yourself.

For that, you need:

* Voice clone the character
* Paraphrase all the replies of the assistant so they match the character personality
* Create the images of the character so you can see them living their lives in the assistant

For the first two tasks, there are working and tested pipelines in `chara` project that you can use.
For the third task, the pipeline is pending.




