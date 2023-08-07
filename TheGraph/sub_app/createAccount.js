const Web3 = require('web3');
const web3 = new Web3('http://ganache:8545'); // Замените URL на URL вашей ноды Ethereum

const createAccount = async () => {
  const account = web3.eth.accounts.create();
  console.log("New account created:");
  console.log("Address:", account.address);
  console.log("Private Key:", account.privateKey);
};

createAccount();
