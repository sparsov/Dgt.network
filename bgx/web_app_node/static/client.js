// get DOM elements
var from      = document.getElementById('from'),
    to        = document.getElementById('to');
    amount    = document.getElementById('amount');
    send      = document.getElementById('send');
    addresses = document.getElementById('addresses');

amount.value = 10

send.addEventListener('click', function(ev){
  getSinature();
  ev.preventDefault();
}, false);

function sentTx(payload, signature) {
    // get result
    var xhr = new XMLHttpRequest();
    xhr.open("POST", `http://localhost:8008/transactions`, true);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log(xhr);
            var json = JSON.parse(xhr.responseText);
            console.log(json);
        }
    };
    var data = JSON.stringify({data: {payload: payload, signed_payload: signature}});
    console.log(data);
    xhr.send(data);
}

function getSinature() {
    var payload = {
        'address_from': from.value,
        'address_to': to.value,
        'tx_payload': amount.value,
        'coin_code': 'bgt',
    }

    // get result
    var xhr = new XMLHttpRequest();
    xhr.open("POST", `http://localhost:8000/sign`, true);
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
    xhr.open("GET", `http://localhost:8000/addresses`, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var json = JSON.parse(xhr.responseText);
            json.addresses.forEach(function(el) {
                var li = document.createElement("li");
                li.appendChild(document.createTextNode(el));
                addresses.appendChild(li);
            })
            from.value = json.addresses[0]
            to.value = json.addresses[1]
        }
    };
    xhr.send();
}
getAddresses()
