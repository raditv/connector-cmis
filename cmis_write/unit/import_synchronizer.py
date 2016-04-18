# -*- coding: utf-8 -*-
# © 2014-2015 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
from openerp.addons.connector.queue.job import job

_logger = logging.getLogger(__name__)


@job
def create_doc_in_edm(session, model_name, res,
                      dict_metadata, user_login, filters=None):
    """
    This method allows to create a doc from Odoo to DMS
    """
    ir_attach = session.env['ir.attachment'].browse(res)
    ir_attach_doc_backend_obj = session.env['ir.attachment.doc.backend']

    # List of backend with storing_ok is True
    backends = session.env['cmis.backend'].search(
        [('storing_ok', '=', 'True')])

    for backend in backends:
        try:
            repo = backend.check_auth()
            root = repo.rootFolder
            folder_path = backend.initial_directory_write
            # Document properties
            file_name = ir_attach.name
            props = {
                'cmis:name': ir_attach.name,
                'cmis:description': ir_attach.description,
                'cmis:createdBy': user_login,
            }
            # Add list of metadata in props
            if len(dict_metadata):
                for k, v in dict_metadata.iteritems():
                    props[k] = v
            if folder_path:
                sub1 = repo.getObjectByPath(folder_path)
            else:
                sub1 = root
            someDoc = sub1.createDocumentFromString(
                file_name,
                contentString=base64.b64decode(
                    ir_attach.datas), contentType=ir_attach.mimetype
            )
            # TODO: create custom properties on a document (Alfresco)
            # someDoc.getProperties().update(props)
            # Updating ir.attachment object with the new id
            # of document generated by DMS
            ir_attach.write({
                'id_dms': someDoc.getObjectId(),
                'datas': None})
            ir_attach_doc_backend_obj.create({
                    'attachment_id': res,
                    'cmis_backend_id': backend.id,
                    'object_doc_id': ir_attach.id_dms,
                })
            _logger.warn('Attachment saved in DMS %s', backend.name)
        except:
            _logger.warn('Cannot save the attachment in DMS %s', backend.name)
            continue
    return True
