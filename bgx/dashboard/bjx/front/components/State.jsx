import React from 'react'
import { connect } from 'react-redux'
import classNames from 'classnames/bind'
import Hash from './Hash'

class State extends React.Component {
  render() {
      const {state, className, id, role} = this.props;

      if (!state.length)
        return (<div className={className} id={id} role={role}>
          <strong> No State</strong>
          </div>)
      else
          return (
            <div className={className} id={id} role={role}>
              <table className={classNames('table', 'table-bordered', 'table-sm', 'table-striped')}>
                <thead>
                  <tr>
                    <th>address</th>
                    <th>data</th>
                  </tr>
                </thead>
                <tbody>
              {state.map((t) => {
                return (
                    <tr>
                      <td><Hash hash={t.address}/></td>
                      <td><Hash hash={t.data}/></td>
                    </tr>
                  )
              })}
              </tbody>
              </table>
            </div>
          )
  }
}

State.defaultProps = {
  state: [],
};

function mapStateToProps(store) {
  return {
    state: store.stateReducer.data,
  };
}

export default connect (mapStateToProps, null)(State);
