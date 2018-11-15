var os = require('os');
if (os.platform() == 'win32') {
    var chilkat = require('chilkat_node10_win32');
} else if (os.platform() == 'linux') {
    if (os.arch() == 'arm') {
        var chilkat = require('chilkat_node10_arm');
    } else if (os.arch() == 'x86') {
        var chilkat = require('chilkat_node10_linux32');
    } else {
        var chilkat = require('chilkat_node10_linux64');
    }
} else if (os.platform() == 'darwin') {
    var chilkat = require('chilkat_node10_macosx');
}
var glob = new chilkat.Global();
var success = glob.UnlockBundle("Anything for 30-day trial");

var addressesToPrivKeys = {
    "4aa37a37b9793a7f3696129d9a367b26fd0b2b1c": "MC4CAQEEIN5I3Rd3U/0uZ9D+3qY/12U8X8XTti73YpId2QUnzEZUoAcGBSuBBAAK",
    "673fcacfb51214e0543b786da79956b541e7d792": "MC4CAQEEIEl8UH0qpL7Xj3LvTY8m3TtiMBJDOhm+qtRdvjH4ADUaoAcGBSuBBAAK",
    "d7d24d1c1ca78c63769ea99d563cb259311d2d62": "MC4CAQEEIEBR/EcoAQi+1c+YVrtx+6XgX6jlqLKZvaie4yfdFOyMoAcGBSuBBAAK"
}
const express = require('express')
var bodyParser = require('body-parser')
const app = express();
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies
app.use(express.static(__dirname + '/static'));
// app.use(express.static(__dirname));

// app.get('/', (req, res) => {
//   res.sendFile(__dirname + '/views/index.html')
// });

app.get('/addresses', (req, res) => {
    res.json({addresses: Object.keys(addressesToPrivKeys)})
});

app.post('/sign', (req, res) => {
    payload = req.body
    var crypt = new chilkat.Crypt2();
    crypt.HashAlgorithm = "SHA256";
    crypt.Charset = "utf-8";
    crypt.EncodingMode = "base64";
    var serializedPayload = ''
    Object.keys(payload).sort().forEach((el) => {
        serializedPayload += `"${el}": "${payload[el]}", `
    })
    serializedPayload = `{${serializedPayload.slice(0, -2)}}`
    var hash = crypt.HashStringENC(serializedPayload);
    var privKey = new chilkat.PrivateKey();
    var bufferData = Buffer.from(addressesToPrivKeys[payload.address_from])
    privKey.LoadPkcs1(bufferData)
    var prng = new chilkat.Prng();
    //  Sign the hash..
    var ecdsa = new chilkat.Ecc();
    var ecdsaSigBase64 = ecdsa.SignHashENC(hash,"base64",privKey,prng);

    res.send({signature: ecdsaSigBase64})
});

app.listen(8000, () => {
  console.log('BGX Example app listening on port 8000!')
});
