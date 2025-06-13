let SESSION_ID = ''
// Set your own BASE_URL
// Setting empty string means all requests will be made to /
const BASE_URL = ''

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
    audio_is_playing = true
    const audio_control = new Audio(`${BASE_URL}/file/${payload['filename']}`)
    audio_control.play()
    audio_control.addEventListener("ended", () => {
        fetch(`${BASE_URL}/command/${SESSION_ID}/confirmation_audio`, {
            method: "POST",
            body: JSON.stringify(payload['filename']),
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
        })
        setTimeout(updates,1)
    })
}

function add_image(payload) {
    image_control = document.getElementById("main_image")
    image_control.src = `${BASE_URL}/file/${payload['filename']}`
}


function add_buttons(payload) {
  const overlay = document.getElementById('overlay');
  overlay.innerHTML = '';

  if (!payload) {
    overlay.style.display = 'none';
    return;
  }

  overlay.style.display = 'grid';
  overlay.style.gridTemplateColumns = `repeat(${payload.width}, 1fr)`;
  overlay.style.gridTemplateRows = `repeat(${payload.height}, 50px)`;
  overlay.style.gap = '5px';

  for (const btn of payload.buttons) {
    const button = document.createElement('button');
    button.textContent = btn.text;
    button.className = 'grid-button';

    button.style.gridColumn = `${btn.column + 1} / span ${btn.column_span || 1}`;
    button.style.gridRow = `${btn.row + 1} / span ${btn.row_span || 1}`;

    overlay.appendChild(button);
  }
}


function process_updates(data) {
    initialize_next = false

    for (const element of data) {
        if (element['id'] > last_message) {
            last_message = element['id']
        }
        else {
            continue
        }
        if (element['type'] == 'reaction_message') {
            add_message(element['payload'])
        }
        if (element['type'] == 'reaction_image') {
            add_image(element['payload'])
        }
        if (element['type'] == 'reaction_audio') {
            add_sound(element['payload'])
            return
        }
        if (element['type'] == 'notification_driver_start') {
            initialize_next = true
        }
        if (element['type'] == 'overlay_buttons') {
            add_buttons(element['payload'])
        }
    }

    if (initialize_next) {
        setTimeout(initialize,1)
    }
    else {
        setTimeout(updates,1000)
    }
}


function updates() {
  fetch(`${BASE_URL}/updates/${SESSION_ID}/${last_message}`)
  .then(response => response.json())
  .then(data => process_updates(data))
  .catch(err => {
        msg = "Error in updates:\n"+err
        console.warn(msg, err)
        add_message({
            type: "Error",
            message: msg,
            sender: null,
            avatar: null
        })
  })
}

function initialize() {
    control = document.getElementById("chat")
    control.innerHTML = ''

    session_control = document.getElementById("customSessionIdHolder")
    SESSION_ID = session_control.innerText
    if (SESSION_ID == '***SESSION_ID***') {
        SESSION_ID = Math.floor(Math.random() * 1000000).toString()
    }

    fetch(`${BASE_URL}/command/${SESSION_ID}/command_initialize`, {
      method: "POST",
      body: JSON.stringify(''),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
    })
    .then(response => response.json())
    .then(data=> {
            last_message=data.id
            setTimeout(updates,1)
    })
    .catch(err => {
        msg = "Error in initialization:\n"+err
        console.warn(msg, err)
        add_message({
            type: "Error",
            message: msg,
            sender: null,
            avatar: null
        })
    })

}

addEventListener("load", (event) => initialize());