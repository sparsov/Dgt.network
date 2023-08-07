const Web3 = require('web3');
const web3 = new Web3('http://ganache:8545'); // Замените URL на URL вашей ноды Ethereum

module.exports = async function(callback) {
  const accounts = await web3.eth.getAccounts();

  for (const account of accounts) {
    const balance = await web3.eth.getBalance(account);
    console.log(`Account: ${account}`);
    console.log(`Balance: ${web3.utils.fromWei(balance, 'ether')} ETH`);
    console.log('Gas Price:', await web3.eth.getGasPrice());
    console.log('------------------------');
  }

  callback();
};

