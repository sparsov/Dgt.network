import React from 'react'
import Transaction from './Transaction'
import { connect } from 'react-redux'
import classNames from 'classnames/bind'

class Transactions extends React.Component {
  render() {
    const {transactions, className, id, role} = this.props

    if (!transactions.length)
      return (<div className={className} id={id} role={role}>
        <strong> No transactions</strong>
        </div>)
    else
      return (<div className={className} id={id} role={role}>
        <table className={classNames('table', 'table-bordered', 'table-sm', 'table-striped')}>
          <thead>
            <tr>
              <th>family name (family version)</th>
              <th>inputs</th>
              <th>outputs</th>
              <th><i>from</i></th>
              <th><i>to</i></th>
              <th>signer_public_key</th>
            </tr>
          </thead>
          <tbody>
        {transactions.map((t) => {
          return <Transaction key={t.header_signature} t={t}/>
        })}
        </tbody>
        </table>
      </div>)
  }
}

Transactions.defaultProps = {
  transactions: [],
};

function mapStateToProps(store) {
  return {
    transactions: store.transactionReducer.data,
  };
}

export default connect (mapStateToProps, null)(Transactions);
