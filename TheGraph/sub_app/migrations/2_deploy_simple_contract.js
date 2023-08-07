const SimpleContract = artifacts.require("SimpleContract");

module.exports = function (deployer) {
  deployer.deploy(SimpleContract, 42); // Передаем начальное значение (в данном случае, 100)
};
