const SESSION_ID = Math.floor(Math.random() * 1000000).toString()
// Set your own BASE_URL
// Setting empty string means all requests will be made to /
const BASE_URL = 'http://localhost:8890'

let audio_is_playing = false
let last_message = 0

function build_message_p(payload) {
    p = ''
    p+='<p class = "';

    if (payload['type'] == 'FromUser') p+='right'
    else p+='left'
    p+='" '

    if (payload['avatar']) p+='style="background-image: url('+"'"+`${BASE_URL}${payload['avatar']}`+"'"+');" '

    p+=">"
    p+=payload['text']
    p+="</p>"
    return p
}

function add_message(payload) {
    html_addition = build_message_p(payload)
    control = document.getElementById("chat")
    control.innerHTML += html_addition
    control.scrollTop = control.scrollHeight
}

function add_sound(payload) {
    if (audio_is_playing) {
        return
    }

    const audio_control = new Audio(`${BASE_URL}/file/${payload['filename']}`)
    audio_control.play().then(() => audio_is_playing = true)
    audio_control.addEventListener("ended", () => audio_is_playing = false)
}

function add_image(payload) {
    image_control = document.getElementById("main_image")
    image_control.src = `${BASE_URL}/file/${payload['filename']}`
}

function process_updates(data) {
    new_last_message_id = last_message
    html_addition = ''
    image = null
    play_queue = []

    for (const element of data) {
        if (element['type'] == 'reaction_message') {
            add_message(element['payload'])
        }
        if (element['type'] == 'reaction_image') {
            add_image(element['payload'])
        }
        if (element['type'] == 'reaction_audio') {
            add_sound(element['payload'])
        }
        if (element['id'] > new_last_message_id) {
            last_message = element['id']
        }
    }
}


function updates() {
  fetch(`${BASE_URL}/updates/${SESSION_ID}/${last_message}`)
  .then(response => response.json())
  .then(data => process_updates(data))
  .catch(err => console.warn('Something went wrong.', err))
}

function initialize() {
    control = document.getElementById("chat")
    control.innerHTML = ''

    fetch(`${BASE_URL}/command/${SESSION_ID}/command_initialize`, {
      method: "POST",
      body: JSON.stringify(''),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
    });
}

addEventListener("load", (event) => initialize());
setInterval(updates, 1000)