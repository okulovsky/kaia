var session_id =  Math.floor(Math.random() * 1000000).toString()
var last_message = 0

function build_message_p(payload) {
    p = ''
    p+='<p class = "';

    if (payload['type'] == 'FromUser') p+='right'
    else p+='left'
    p+='" '

    if (payload['avatar']) p+='style="background-image: url('+"'"+payload['avatar']+"'"+');" '

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
    var audio_control = new Audio('/file/'+payload['filename'])
    audio_control.play()
}

function add_image(payload) {
    image_control = document.getElementById("main_image")
    image_control.src = '/file/' + payload['filename']
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
  fetch('/updates/'+session_id+"/"+last_message)
  .then(response => response.json())
  .then(data => process_updates(data))
  .catch(err => console.warn('Something went wrong.', err))
}

function initialize() {
    control = document.getElementById("chat")
    control.innerHTML = ''


    fetch("/command/"+session_id+"/command_initialize", {
      method: "POST",
      body: JSON.stringify(''),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
    });
}

addEventListener("load", (event) => initialize());
setInterval(updates, 1000)