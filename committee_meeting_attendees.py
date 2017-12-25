from datapackage_pipelines.wrapper import ingest, spew
import logging, requests
from knesset_data.protocols.committee import CommitteeMeetingProtocol


parameters, datapackage, resources = ingest()
aggregations = {"stats": {}}
kns_committeesession_resource, kns_committeesession_descriptor = None, None


for descriptor, resource in zip(datapackage["resources"], resources):
    if descriptor["name"] == "kns_committeesession":
        kns_committeesession_descriptor, kns_committeesession_resource = descriptor, resource
    else:
        for row in resource:
            pass


def get_kns_committeesession_resource():
    for committeesession_row in kns_committeesession_resource:
        if (
            (not parameters.get("filter-meeting-id") or int(committeesession_row["CommitteeSessionID"]) in parameters["filter-meeting-id"])
            and (not parameters.get("filter-committee-id") or int(committeesession_row["CommitteeID"]) in parameters["filter-committee-id"])
            and (not parameters.get("filter-knesset-num") or int(committeesession_row["KnessetNum"]) in parameters["filter-knesset-num"])
        ):
            if committeesession_row["text_object_name"]:
                protocol_text_url = "https://minio.oknesset.org/committees/" + committeesession_row["text_object_name"]
                text = requests.get(protocol_text_url).content.decode("utf-8")
                with CommitteeMeetingProtocol.get_from_text(text) as protocol:
                    committeesession_row.update(protocol.attendees)
            yield committeesession_row


kns_committeesession_descriptor["schema"]["fields"] += [{"name": "mks", "type": "array"},
                                                        {"name": "invitees", "type": "array"},
                                                        {"name": "legal_advisors", "type": "array"},
                                                        {"name": "manager", "type": "array"},]


spew(dict(datapackage, resources=[kns_committeesession_descriptor]),
     [get_kns_committeesession_resource()],
     aggregations["stats"])
