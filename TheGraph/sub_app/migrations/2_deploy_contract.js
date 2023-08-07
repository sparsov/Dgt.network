const SimpleToken = artifacts.require("SimpleToken"); // Имя контракта

module.exports = function(deployer,network, accounts) {
  const deployerAccountIndex = 0;
  const initialSupply = 1000000; // Здесь указывается начальное количество токенов
  deployer.deploy(SimpleToken, initialSupply,{ from: accounts[deployerAccountIndex] });
};
