import React from 'react'
import Hash from './Hash'

class Transaction extends React.Component {
  render() {
    const { t } = this.props;
    return (<tr>
      <td> {t.header.family_name} ( {t.header.family_version}) </td>
      <td>
        {t.header.inputs.map((i) => {
          return (  <Hash key={i} hash={i}/> )
        })}
        </td>
      <td>
        {t.header.outputs.map((i) => {
          return (  <Hash key={i} hash={i}/> )
        })}
      </td>
      <td><i>wallet key</i></td>
      <td><i>wallet key</i></td>
      <td>
        <Hash hash={t.header.signer_public_key}/>
      </td>
      </tr>);
  }
}

export default Transaction;
