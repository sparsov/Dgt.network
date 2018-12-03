import { trimHash } from '../helpers/helper'

export function convertBlocks(data) {
    let parent = {name: 'initial'}
    let initial = parent
    data.data.forEach((i) => {

      let node = {
        name: trimHash(i.header_signature),
        children: []
      }
      parent.children = [node]
      parent = node
    })
  return initial.children[0];
}
