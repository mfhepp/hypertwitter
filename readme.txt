README.TXT

This application is live at http://semantictwitter.appspot.com.

In order to deploy your own version to the Google App Engine, you need to create a symbolic link named

rdflib

into the root directory of the application. The symbolic link must point to the local address of the RDFlib package on the machine used for deploying the application, e.g.

/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/rdflib-2.4.2/rdflib

The Google App Engine tools will then find and transfer the RDFlib sources to the Google server when deploying the app.

If you have any questions, please contact martin.heppATunibw.de



