__autor__ = 'nickbortolotti'
__licencia__ = 'Apache 2.0'

import os
import sys
import simplejson
import jinja2
import webapp2

from apiclient.discovery import build
from oauth2client.appengine import OAuth2DecoratorFromClientSecrets

#Decorador para el cliente de BigQuery - ** Recuerde utilizar su client_secrets.json **
decorator = OAuth2DecoratorFromClientSecrets(os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
                                             scope='https://www.googleapis.com/auth/bigquery')

#Construccion del servicio de BigQuery
servicio = build('bigquery', 'v2')

#Variables del proyecto
Proyecto = 'socialagilelearning'
Dataset = "samples"
Consulta = """SELECT title,num_characters FROM publicdata:samples.wikipedia Limit 5;"""

#Entorno Jinja para trabajar plantillas y el HTML
Entorno_Jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Panel(webapp2.RequestHandler):
    @decorator.oauth_required
    def get(self):

        http = decorator.http()
        jobtesting = servicio.jobs()

        try:
            #Creacion de la consulta al banco de datos
            consulta_data = {'query':Consulta,'defaultDataset.datasetId':Dataset}
            Respuesta_Consulta = jobtesting.query(projectId=Proyecto, body=consulta_data).execute(http)

            #Creacion de la estructura de datos para insertar en el grafico
            columnNameID = Respuesta_Consulta['schema']['fields'][0]['name']
            columnNameValores = Respuesta_Consulta['schema']['fields'][1]['name']

            #Definicion de los datos a trabajar
            chart_data = dict(cols=({'id': columnNameID, 'label': columnNameID, 'type': 'string'},
                             {'id': columnNameValores, 'label': columnNameValores, 'type': 'number'}))

            chart_data['rows'] = [];

            #Iteracion de datos
            for row in Respuesta_Consulta['rows']:
                nrow = ({'c':[]})
                nrow['c'].append({'v': row['f'][0]['v']})
                nrow['c'].append({'v':row['f'][1]['v']})
                chart_data['rows'].append(nrow)

            #Formacion del json con la estructura para el grafico
            data = simplejson.dumps(chart_data)
            query = Consulta

            #Definicion de los datos para insertar en HTML. Jinja2
            plantilla_values = {
                'data': data,
                'query': query,
            }

            #Inferencia de la plantilla con el HTML correspondiente
            template = Entorno_Jinja.get_template('polymerUI/index.html')
            self.response.write(template.render(plantilla_values))

        except:
            e = str(sys.exc_info()[0]).replace('&', '&amp;'
            ).replace('"', '&quot;'
            ).replace("'", '&#39;'
            ).replace(">", '&gt;'
            ).replace("<", '&lt;')
            self.response.out.write("<p>Error: %s</p>" % e)


application = webapp2.WSGIApplication([
                                         ('/', Panel),
                                         (decorator.callback_path, decorator.callback_handler()),
                                     ], debug=True)