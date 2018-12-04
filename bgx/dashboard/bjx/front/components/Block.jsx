import React from 'react'
import Hash from './Hash'

class Block extends React.Component {
  render() {
    const { t } = this.props;
    return (<tr>
      <td> {t.header.block_num} </td>
      <td>
        {t.header.batch_ids.map((i) => {
          return (  <Hash key={i} hash={i}/> )
        })}
      </td>
      <td> {t.header.consensus} </td>
      <td> <Hash hash={t.header.previous_block_id}/> </td>
      <td><Hash hash= {t.header.signer_public_key}/> </td>
      <td> <Hash hash={t.header.state_root_hash}/> </td>
      </tr>);
  }
}

export default Block;
