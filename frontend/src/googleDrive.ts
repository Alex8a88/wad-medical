import { gapi } from 'gapi-script';

const CLIENT_ID = '459005759009-q35d1kd3cpke3n5fv8t8ccspv5vevdcs.apps.googleusercontent.com';
const API_KEY = 'AIzaSyCcnqsI5au0DCB1K1CXrlVD5F-eihTMtJg';
const DISCOVERY_DOC = 'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest';
const SCOPES = 'https://www.googleapis.com/auth/drive.file';
const FOLDER_ID = '1mNEOtJcX90E3N3WMi2knv8tiJ7x0Am93';

export const initializeGapi = async () => {
  await gapi.load('client', async () => {
    await gapi.client.init({
      apiKey: API_KEY,
      discoveryDocs: [DISCOVERY_DOC],
    });
  });
};



export const signIn = async () => {
  return new Promise((resolve, reject) => {
    // @ts-ignore
    window.google.accounts.oauth2.initTokenClient({
      client_id: CLIENT_ID,
      scope: SCOPES,
      callback: (tokenResponse: any) => {
        if (tokenResponse.error) {
          reject(tokenResponse.error);
        } else {
          gapi.client.setToken(tokenResponse);
          resolve(tokenResponse);
        }
      },
    }).requestAccessToken();
  });
};

export const generatePatientXML = (formData: any, numAfiliacion: string) => {
  const now = new Date();
  const timestamp = now.toISOString();
  
  // Format phone number as XX-XXXX-XXXX
  const phone = formData.numero_telefono;
  const formattedPhone = phone.length >= 10 ? 
    `${phone.slice(0,2)}-${phone.slice(2,6)}-${phone.slice(6,10)}` : phone;
  
  // Generate checksum (simple hash)
  const dataString = `${formData.primer_nombre}${formData.primer_apellido}${formData.email_usuario}${timestamp}`;
  const checksum = btoa(dataString).slice(0, 16);
  
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<paciente>
  <num_afiliacion>${numAfiliacion}</num_afiliacion>
  <datos_personales>
    <primer_nombre>${formData.primer_nombre}</primer_nombre>
    <segundo_nombre>${formData.segundo_nombre || ''}</segundo_nombre>
    <primer_apellido>${formData.primer_apellido}</primer_apellido>
    <segundo_apellido>${formData.segundo_apellido || ''}</segundo_apellido>
    <nombre_completo>${formData.primer_nombre}${formData.segundo_nombre ? ' ' + formData.segundo_nombre : ''} ${formData.primer_apellido}${formData.segundo_apellido ? ' ' + formData.segundo_apellido : ''}</nombre_completo>
    <edad>${formData.edad}</edad>
    <genero>${formData.genero}</genero>
  </datos_personales>
  <datos_medicos>
    <tipo_sangre>${formData.tipo_sangre}</tipo_sangre>
    <alergias>${formData.alergias || 'Ninguna'}</alergias>
  </datos_medicos>
  <contacto>
    <email_usuario>${formData.email_usuario}</email_usuario>
    <numero_telefono>${formattedPhone}</numero_telefono>
  </contacto>
  <direccion>
    <calle>${formData.calle}</calle>
    <num_ext>${formData.num_ext}</num_ext>
    <num_int>${formData.num_int || ''}</num_int>
    <colonia>${formData.colonia}</colonia>
    <ciudad>${formData.ciudad}</ciudad>
    <estado>${formData.estado}</estado>
    <c_postal>${formData.c_postal}</c_postal>
  </direccion>
  <metadatos>
    <origen>WEB</origen>
    <fecha_evento>${timestamp}</fecha_evento>
    <operacion>ALTA</operacion>
    <checksum>${checksum}</checksum>
  </metadatos>
</paciente>`;
  
  return xml;
};

export const uploadToGoogleDrive = async (xmlContent: string, fileName: string) => {
  const boundary = '-------314159265358979323846';
  const delimiter = "\r\n--" + boundary + "\r\n";
  const close_delim = "\r\n--" + boundary + "--";

  const metadata = {
    'name': fileName,
    'parents': [FOLDER_ID]
  };

  const multipartRequestBody =
    delimiter +
    'Content-Type: application/json\r\n\r\n' +
    JSON.stringify(metadata) +
    delimiter +
    'Content-Type: application/xml\r\n\r\n' +
    xmlContent +
    close_delim;

  const request = gapi.client.request({
    'path': 'https://www.googleapis.com/upload/drive/v3/files',
    'method': 'POST',
    'params': {'uploadType': 'multipart'},
    'headers': {
      'Content-Type': 'multipart/related; boundary="' + boundary + '"'
    },
    'body': multipartRequestBody
  });

  return request;
};