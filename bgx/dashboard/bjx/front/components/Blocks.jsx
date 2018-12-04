import React from 'react'
import { connect } from 'react-redux'
import classNames from 'classnames/bind'

import Block from './Block'

class Blocks extends React.Component {

  componentDidUpdate() {

    const data = Object.assign({}, this.props.graph_blocks);

    var width = 600,
        height = 300,
        root;

    var force = d3.layout.force()
        .linkDistance(80)
        .charge(-120)
        .gravity(.05)
        .size([width, height])
        .on("tick", tick);

    var svg = d3.select(".chart-block")
        .attr("width", width)
        .attr("height", height);

    var link = svg.selectAll(".link"),
        node = svg.selectAll(".node");

    // d3.json("graph.json", function(error, json) {
    //   if (error) throw error;

      root = data;
      update();
    // });

    function update() {
      var nodes = flatten(root),
          links = d3.layout.tree().links(nodes);

      // Restart the force layout.
      force
          .nodes(nodes)
          .links(links)
          .start();

      // Update links.
      link = link.data(links, function(d) { return d.target.id; });

      link.exit().remove();

      link.enter().insert("line", ".node")
          .attr("class", "link");

      // Update nodes.
      node = node.data(nodes, function(d) { return d.id; });

      node.exit().remove();

      var nodeEnter = node.enter().append("g")
          .attr("class", "node")
          .on("click", click)
          .call(force.drag);

      nodeEnter.append("circle")
          .attr("r", function(d) { return Math.sqrt(d.size) / 10 || 4.5; });

      nodeEnter.append("text")
          .attr("dy", ".35em")
          .text(function(d) { return d.name; });

      node.select("circle")
          .style("fill", color);
    }

    function tick() {
      link.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });

      node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
    }

    function color(d) {
      return d._children ? "#3182bd" // collapsed package
          : d.children ? "#c6dbef" // expanded package
          : "#fd8d3c"; // leaf node
    }

    // Toggle children on click.
    function click(d) {
      if (d3.event.defaultPrevented) return; // ignore drag
      if (d.children) {
        d._children = d.children;
        d.children = null;
      } else {
        d.children = d._children;
        d._children = null;
      }
      store.dispatch(selectP(d))
      update();
    }

    // Returns a list of all nodes under the root.
    function flatten(root) {
      var nodes = [], i = 0;

      function recurse(node) {
        if (node.children) node.children.forEach(recurse);
        if (!node.id) node.id = ++i;
        nodes.push(node);
      }

      recurse(root);
      return nodes;
    }
  }

  render() {
    const {graph_blocks, blocks_data, className, id, role} = this.props;

    if (graph_blocks == null)
    return (
      <div className={className} id={id} role={role}>
        <strong> No Blocks</strong>
      </div>)
    else
      return (
        <div className={className} id={id} role={role}>
          <div classNmae='row'>
            <div className='col-6'>
              <div className='container'>
                <div className='chartContainer'>
                  <svg className='chart-block'/>
                </div>
              </div>
            </div>

            <div className='col-6'>

              <table className={classNames('table', 'table-bordered', 'table-sm', 'table-striped')}>
                <thead>
                  <tr>
                    <th>Block Num</th>
                    <th>Batch Ids</th>
                    <th>Consensus</th>
                    <th>Previous block ID</th>
                    <th>signer_public_key</th>
                    <th>state root hash</th>
                  </tr>
                </thead>
                <tbody>
                {blocks_data.map((t) => {
                  return <Block key={t.header_signature} t={t}/>
                })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )
  }
}

Blocks.defaultProps = {
  graph_blocks: null,
  blocks_data: [],
};

function mapStateToProps(store) {
  return {
    graph_blocks: store.blocksReducer.data.graph,
    blocks_data: store.blocksReducer.data.data,
  };
}

export default connect (mapStateToProps, null)(Blocks);
