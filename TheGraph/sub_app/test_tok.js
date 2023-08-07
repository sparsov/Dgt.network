const Web3 = require('web3');
const web3 = new Web3('http://ganache:8545'); // Подставьте ваш порт для Ganache

const SimpleToken = artifacts.require("SimpleToken");
//const senderAccount = web3.eth.accounts[0]; 

module.exports = async function(callback) {
  try {
    const instance = await SimpleToken.deployed();
    const accounts = await web3.eth.getAccounts();
    const senderAccount = accounts[0];
    console.log("SimpleToken loaded",senderAccount);
    console.log("ask  totalSupply");
    const totalSupply = await instance.totalSupply();
    console.log("Total Supply:", totalSupply.toString());
    const decimals = await instance.decimals();
    console.log("decimals:", decimals.toString());
    //const totalSupply = await instance.getTotalSupply();
    //console.log("Total Supply:", totalSupply.toString());
    // Пример вызова функции transfer:0xRecipientAddress  "0xA962B58709a7882d38A4fF415e8913F622767D32",
   await instance.transfer("0xa402Ed4AeE536788a220ed8ba5633EE361E05c08", web3.utils.toWei("1", "ether"));

    // Пример вызова функции approve:"0xSpenderAddress""0xA962B58709a7882d38A4fF415e8913F622767D32"
    await instance.approve("0xa402Ed4AeE536788a220ed8ba5633EE361E05c08", web3.utils.toWei("0.5", "ether"));

    // Пример вызова функции transferFrom:
    await instance.transferFrom("0xa402Ed4AeE536788a220ed8ba5633EE361E05c08",senderAccount,  web3.utils.toWei("0.5", "ether"));

    console.log("Function calls completed successfully.");
  } catch (error) {
    console.error("Error:", error);
  }

  callback();
};

