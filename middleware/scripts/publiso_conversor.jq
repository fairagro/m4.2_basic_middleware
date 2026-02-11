.[] | {
    "@context": {
        "@language": "en",
        "@vocab":"https://schema.org/"},
    "@type": "Dataset",
    "@id":
        (if has("doi")
            then "https://doi.org/" + .doi
            else "https://repository.publisso.de/resource/" + .["@id"]
        end),
    "name": (if has("title") then (.title[]) else null end),
    "alternativeHeadline": (if has("alternative") then .alternative[0] else null end),
    "description": (if has("description") then (.description[]) else null end),
    "identifier": ([
        (if has("doi") then
            {
              "@type": "PropertyValue",
              "propertyID": "https://registry.identifiers.org/registry/doi",
              "value": .doi,
              "url": ("https://doi.org/" +  .doi)
            }
         else empty end),
        {
          "@type": "PropertyValue",
          "propertyID": "frl-internal",
          "value": .["@id"],
          "url": ("https://repository.publisso.de/resource/" +  .["@id"])
        }
    ]),

    "creator":
        [
            (if has("creator") then
                (.creator[]
                  | {
                      "@type": "Person",
                      "familyName": (.prefLabel | split(", ")[0]),
                      "givenName":  (.prefLabel | split(", ")[1: ] | join(" ")),
                      "identifier": ."@id"
                    }
                )
            else null end)
        ],
    "contributor":
        [
            (if has("contributor") then
                (.contributor[]
                  | {
                      "@type": "Person",
                      "familyName": (.prefLabel | split(", ")[0]),
                      "givenName":  (.prefLabel | split(", ")[1: ] | join(" ")),
                      "identifier": ."@id"
                    }
                )
            else null end)
        ],
    "sourceOrganization":
        [
            (if has("institution") then (.institution[] | {"@type":"Organization", "@id": ."@id", "name": .prefLabel}) else null end)
        ],
    "datePublished": (if has("issued") then (.issued) else null end),
    "copyrightYear": (if has("yearOfCopyright") then (.yearOfCopyright[0]) else null end),
    "keywords":
        [
            (if has("ddc") then (.ddc[] | {"@type":"DefinedTerm", "name": .prefLabel, "identifier": ."@id", "inDefinedTermSet": "https://www.oclc.org/en/dewey.html"}) else null end),
            (if has("subject") then (.subject[] | {"@type":"DefinedTerm", "name": .prefLabel, "identifier": ."@id"}) else null end)
        ],
    "measurementTechnique":
        [
            (if has("dataOrigin") then (.dataOrigin[] | {"@type":"DefinedTerm", "name": .prefLabel, "identifier": ."@id"}) else null end)
        ],
    "funder":
        [
            (if has("fundingId") then (.fundingId[] | {"@type":"Organization", "@id": ."@id", "name": .prefLabel}) else null end)
        ],
    "funding":
        [
            (if has("joinedFunding") then (.joinedFunding[] | {"@type":"Grant", "name": .fundingProgramJoined, "funder": .fundingJoined | {"@type":"Organization", "@id": ."@id", "name": .prefLabel}}) else (if has("fundingProgram") then (.fundingProgram[] | {"@type":"Grant", "name": .}) else null end) end)
        ],
    "distribution":
        [
            (if has("hasPart") then (.hasPart[] | {"@type":"DataDownload", "@id": ("https://repository.publisso.de/resource/" + ."@id"), "name": .prefLabel}) else null end)
        ],
    "inLanguage":
        [
            (if has("language") then (.language[] | {"@type":"Language", "@id": ."@id", "name": .prefLabel}) else null end)
        ],
    "license": (if has("license") then (.license[]."@id") else null end),
    "spatial":
        [
            (if has("recordingCoordinates") then (.recordingCoordinates[] | {"@type":"Place", "url": ."@id"}) else null end),
            (if has("recordingLocation") then (.recordingLocation[] | {"@type":"Place", "name": .prefLabel, "url": ."@id"}) else null end)
        ]
    } | del(..|nulls) 