from django.test import TestCase

import requests_mock
from privates.test import temp_private_root
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.registrations.constants import RegistrationAttribute
from openforms.registrations.contrib.zgw_apis.plugin import ZGWRegistration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from .factories import ZgwConfigFactory


@temp_private_root()
@requests_mock.Mocker()
class ZGWBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ZgwConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )

    def test_submission_with_zgw_backend(self, m):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geboortedatum,
                    },
                },
            ],
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
            },
            bsn="111222333",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
        )

        zgw_form_options = dict(
            zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            vertrouwelijkheidaanduiding="openbaar",
        )

        mock_service_oas_get(m, "https://zaken.nl/api/v1/", "zaken")
        mock_service_oas_get(m, "https://documenten.nl/api/v1/", "documenten")
        mock_service_oas_get(m, "https://catalogus.nl/api/v1/", "catalogi")

        m.post(
            "https://zaken.nl/api/v1/zaken",
            status_code=201,
            json=generate_oas_component(
                "zaken",
                "schemas/Zaak",
                url="https://zaken.nl/api/v1/zaken/1",
                zaaktype="https://catalogi.nl/api/v1/zaaktypen/1",
            ),
        )
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "documenten",
                        "schemas/EnkelvoudigInformatieObject",
                        url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )
        m.post(
            "https://zaken.nl/api/v1/zaakinformatieobjecten",
            [
                # two calls on same URL: one PDF and one attachment
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken.nl/api/v1/zaakinformatieobjecten/1",
                    ),
                    "status_code": 201,
                },
                {
                    "json": generate_oas_component(
                        "zaken",
                        "schemas/ZaakInformatieObject",
                        url="https://zaken.nl/api/v1/zaakinformatieobjecten/2",
                    ),
                    "status_code": 201,
                },
            ],
        )

        m.get(
            "https://catalogus.nl/api/v1/roltypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1&omschrijvingGeneriek=initiator",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus.nl/api/v1/roltypen/1",
                    )
                ],
            },
        )
        m.post(
            "https://zaken.nl/api/v1/rollen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Rol", url="https://zaken.nl/api/v1/rollen/1"
            ),
        )
        m.get(
            "https://catalogus.nl/api/v1/statustypen?zaaktype=https%3A%2F%2Fcatalogi.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/2",
                        volgnummer=2,
                    ),
                    generate_oas_component(
                        "catalogi",
                        "schemas/StatusType",
                        url="https://catalogus.nl/api/v1/statustypen/1",
                        volgnummer=1,
                    ),
                ],
            },
        )
        m.post(
            "https://zaken.nl/api/v1/statussen",
            status_code=201,
            json=generate_oas_component(
                "zaken", "schemas/Status", url="https://zaken.nl/api/v1/statussen/1"
            ),
        )

        plugin = ZGWRegistration("zgw")
        registration_id, result = plugin.register_submission(
            submission, zgw_form_options
        )
        self.assertEqual(registration_id, "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            result["document"]["url"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )
        self.assertEqual(result["rol"]["url"], "https://zaken.nl/api/v1/rollen/1")
        self.assertEqual(result["status"]["url"], "https://zaken.nl/api/v1/statussen/1")
        self.assertEqual(result["zaak"]["url"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            result["zaak"]["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
        )

        # 12 requests in total, 3 of which are GETs on the OAS and 2 are searches and 2 are the attachment
        self.assertEqual(len(m.request_history), 12)

        create_zaak = m.request_history[1]
        create_zaak_body = create_zaak.json()
        self.assertEqual(create_zaak.method, "POST")
        self.assertEqual(create_zaak.url, "https://zaken.nl/api/v1/zaken")
        self.assertEqual(create_zaak_body["bronorganisatie"], "000000000")
        self.assertEqual(
            create_zaak_body["verantwoordelijkeOrganisatie"],
            "000000000",
        )
        self.assertEqual(
            create_zaak_body["vertrouwelijkheidaanduiding"],
            "openbaar",
        )
        self.assertEqual(
            create_zaak_body["zaaktype"], "https://catalogi.nl/api/v1/zaaktypen/1"
        )

        create_eio = m.request_history[3]
        create_eio_body = create_eio.json()
        self.assertEqual(create_eio.method, "POST")
        self.assertEqual(
            create_eio.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(create_eio_body["bronorganisatie"], "000000000")
        self.assertEqual(create_eio_body["formaat"], "application/pdf")
        self.assertEqual(
            create_eio_body["vertrouwelijkheidaanduiding"],
            "openbaar",
        )
        self.assertEqual(
            create_eio_body["informatieobjecttype"],
            "https://catalogi.nl/api/v1/informatieobjecttypen/1",
        )

        create_zio = m.request_history[4]
        create_zio_body = create_zio.json()
        self.assertEqual(create_zio.method, "POST")
        self.assertEqual(
            create_zio.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
        )
        self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_zio_body["informatieobject"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        create_rol = m.request_history[7]
        create_rol_body = create_rol.json()
        self.assertEqual(create_rol.method, "POST")
        self.assertEqual(create_rol.url, "https://zaken.nl/api/v1/rollen")
        self.assertEqual(create_zio_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_rol_body["roltype"],
            "https://catalogus.nl/api/v1/roltypen/1",
        )
        self.assertEqual(
            create_rol_body["betrokkeneIdentificatie"],
            {
                "voornamen": "Foo",
                "geboortedatum": "2000-12-31",
                "inpBsn": "111222333",
                "voorvoegselGeslachtsnaam": "de",
                "geslachtsnaam": "Bar",
            },
        )

        create_status = m.request_history[9]
        create_status_body = create_status.json()
        self.assertEqual(create_status.method, "POST")
        self.assertEqual(create_status.url, "https://zaken.nl/api/v1/statussen")
        self.assertEqual(create_status_body["zaak"], "https://zaken.nl/api/v1/zaken/1")
        self.assertEqual(
            create_status_body["statustype"],
            "https://catalogus.nl/api/v1/statustypen/1",
        )

        create_attachment = m.request_history[10]
        create_attachment_body = create_attachment.json()
        self.assertEqual(create_attachment.method, "POST")
        self.assertEqual(
            create_attachment.url,
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
        )
        self.assertEqual(create_attachment_body["bestandsnaam"], attachment.file_name)
        self.assertEqual(create_attachment_body["formaat"], attachment.content_type)

        relate_attachment = m.request_history[11]
        relate_attachment_body = relate_attachment.json()
        self.assertEqual(relate_attachment.method, "POST")
        self.assertEqual(
            relate_attachment.url, "https://zaken.nl/api/v1/zaakinformatieobjecten"
        )
        self.assertEqual(
            relate_attachment_body["zaak"], "https://zaken.nl/api/v1/zaken/1"
        )
        self.assertEqual(
            relate_attachment_body["informatieobject"],
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/2",
        )
