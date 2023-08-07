const SimpleToken = artifacts.require("SimpleToken");

module.exports = async function(callback) {
  try {
    const instance = await SimpleToken.deployed();
    const account = "0xa402Ed4AeE536788a220ed8ba5633EE361E05c08"; //"0xA962B58709a7882d38A4fF415e8913F622767D32"; // Замените на адрес аккаунта, который вы хотите проверить

    const balance = await instance.balanceOf(account);
    console.log(`Balance of ${account}:`, balance.toString());
    //
    const account1 = "0xc61a458A0986d2DAe195bFf75a0fF310E2Ca876d"; //"0xA962B58709a7882d38A4fF415e8913F622767D32"; // Замените на адрес аккаунта, который вы хотите проверить

    const balance1 = await instance.balanceOf(account1);
    console.log(`Balance of ${account1}:`, balance1.toString());
  } catch (error) {
    console.error("Error:", error);
  }

  callback();
};
