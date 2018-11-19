// get DOM elements
var REST_API_ENDPOINT = 'http://localhost:8009'
var WEB_SERVER_ENDPOINT = 'http://localhost:8000'

var from      = document.getElementById('from'),
    to        = document.getElementById('to');
    amount    = document.getElementById('amount');
    send      = document.getElementById('send');
    refresh   = document.getElementById('refresh');
    addresses = document.getElementById('addresses');

var addressesArray = []
var wallets = []
amount.value = 10

refresh.addEventListener('click', function(ev){
    updateWallets()
    ev.preventDefault();
}, false);

function updateWallets() {
    Promise.all(getWallets()).then(function(){
        addresses.innerHTML = ''
        wallets.sort()
        wallets.forEach(function(el) {
            var li = document.createElement("li");
            li.appendChild(document.createTextNode(el));
            addresses.appendChild(li);
        })
    })
}

function getWallets() {
    wallets = []
    return addressesArray.map(function(addr) {
        return new Promise(function(resolve, reject) {
            var xhr = new XMLHttpRequest();
            // xhr.responseType = 'json';
            xhr.open("GET", `${REST_API_ENDPOINT}/wallets/${addr}`, true);
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var json = JSON.parse(xhr.responseText);
                    var values = json.data
                    var _keys = Object.keys(values)
                    wallets.push(`${addr} - ${values[_keys[0]].val} ${values[_keys[0]].group}`)
                    resolve()
                }
            };
            xhr.send();
        })
    })
}

send.addEventListener('click', function(ev){
  getSignature();
  ev.preventDefault();
}, false);

function sentTx(payload, signature) {
    // get result
    var xhr = new XMLHttpRequest();
    xhr.open("POST", `${REST_API_ENDPOINT}/transactions`, true);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var json = JSON.parse(xhr.responseText);
        }
    };
    var data = JSON.stringify({data: {payload: payload, signed_payload: signature}});
    xhr.send(data);
}

function getSignature() {
    var payload = {
        'address_from': from.value,
        'address_to': to.value,
        'tx_payload': amount.value,
        'coin_code': 'bgt',
    }

    // get result
    var xhr = new XMLHttpRequest();
    xhr.open("POST", `${WEB_SERVER_ENDPOINT}/sign`, true);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var json = JSON.parse(xhr.responseText);
            sentTx(payload, json.signature)
        }
    };
    var data = JSON.stringify(payload);
    xhr.send(data);
}

function getAddresses() {
    // get result
    var xhr = new XMLHttpRequest();
    // xhr.responseType = 'json';
    xhr.open("GET", `${WEB_SERVER_ENDPOINT}/addresses`, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var json = JSON.parse(xhr.responseText);
            addressesArray = json.addresses
            updateWallets()
            from.value = json.addresses[0]
            to.value = json.addresses[1]
        }
    };
    xhr.send();
}
getAddresses()
