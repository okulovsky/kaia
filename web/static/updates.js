var session_id =  Math.floor(Math.random() * 1000000).toString()
var last_message = 0

function build_message_p(msg) {
    p = ''
    p+='<p class = "';

    if (msg['type'] == 'FromUser') p+='right'
    else p+='left'
    p+='" '

    if (msg['avatar']) p+='style="background-image: url('+"'"+msg['avatar']+"'"+');" '

    p+=">"
    p+=msg['text']
    p+="</p>"
    return p
}


function process_updates(data) {
    new_last_message_id = last_message
    html_addition = ''
    image = null
    play_queue = []

    for (const element of data) {
        if (element['type'] == 'reaction_message') {
            html_addition+=build_message_p(element['payload'])
        }
        if (element['type'] == 'reaction_image') {
            image = element['payload']
        }
        if (element['type'] == 'reaction_audio') {
            play_queue.push(element['payload'])
        }
        if (element['id'] > new_last_message_id) {
            new_last_message_id = element['id']
        }
    }

    last_message = new_last_message_id

    if (html_addition != '') {
        control = document.getElementById("chat")
        control.innerHTML += html_addition
        control.scrollTop = control.scrollHeight
    }

    if (image) {
        image_control = document.getElementById("main_image")
        image_control.src = '/file/' + image
    }

    for (const audio of data) {
        //var audio_control = new Audio('/file/'+audio)
        //audio_control.play()
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