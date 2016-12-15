CommandNet Processor
====================

Listens on a port for incoming natural language input. Does [Named Entity Recognition][1] and generates [Parse Tree][2] of the natural language input (based on the training questions answered by user and bot in Training Portal) and returns it back to the client

## Contributing ##

Unlike most NERs and Parse Tree generators - this program uses non-statistical models to generate Parse Tree and NER. To train the Parse Tree, make changes in src/Controller/commandnet.py and MongoDB database containing surface texts

LICENSE

This program has been made available in under the terms of the GNU Affero General Public License (AGPL). See individual files for details.


[1]: https://en.wikipedia.org/wiki/Named-entity_recognition
[2]: https://en.wikipedia.org/wiki/Parse_tree
