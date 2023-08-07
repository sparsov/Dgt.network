const Web3 = require('web3');
const web3 = new Web3('http://ganache:8545'); // Подставьте ваш порт для Ganache

const SimpleContract = artifacts.require('SimpleContract');

(async () => {
  const SimpleContract = artifacts.require('SimpleContract'); // Переместите это внутрь асинхронной функции
  const contract = await SimpleContract.deployed();

  const accounts = await web3.eth.getAccounts();

  const countBefore = await contract.getCount();
  console.log(`Count before increment: ${countBefore.toNumber()}`);

  // Вызываем метод контракта для увеличения счетчика
  await contract.increment();

  const countAfter = await contract.getCount();
  console.log(`Count after increment: ${countAfter.toNumber()}`);
})();
