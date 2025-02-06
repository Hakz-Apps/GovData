__NOTE: The full research paper is included at [https://github.com/Hakz-Apps/GovData/blob/main/Identity-Linked%20Risks%20on%20Data-Gov.pdf](https://github.com/Hakz-Apps/GovData/blob/main/Identity-Linked%20Risks%20on%20Data-Gov.pdf)__

IDENTITY-LINKED RISKS ON DATA.GOV
=================================
***AND PROPOSED CONTROLS FOR PUBLIC U.S.G. WORKFORCE DATA***

> Abstract—Anonymous public access to government salary data
> enables malicious actors to target the United States Government
> (U.S.G.) workforce. While identity controls cannot prevent
> targeting by sophisticated threat actors, the U.S.G. can mitigate
> cybersecurity risks without reducing transparency by verifying
> user identities, establishing stricter access controls, truncating
> high-fidelity workforce datasets, and limiting foreign access.

# 1. What is Data.Gov?
Since Congress enacted the OPEN Government Act in 2007,
the United States Government (U.S.G.) has begun making its
data available to the public in a variety of open-source formats,
including JavaScript Object Notation (JSON), Comma
Separated Values (CSV), and eXtensible Markup Language
(XML). As part of the Act, the Office of Management and
Budget created a new site in 2009 called "data.gov" which
allows almost any user to anonymously download data from
thousands of Government sources.

# 2. Hypothesis

>"The U.S.G. can mitigate real cybersecurity
>risks without reducing transparency by
>verifying user identities, establishing stricter
>access controls, and truncating high-fidelity
>workforce datasets."

I intend to present artifacts and case studies that highlight the
risks associated with anonymous access to workforce data. At
the conclusion, I intend to summarize my findings and
recommend safeguards through U.S. policy. The research was
limited in scope to workforce salary data available on data.gov.
The research was further focused on five areas of ongoing
concern: Inference, Doxing, Phishing / Whaling, Workforce
Attrition, and Malign Influence.

# 3. Methodology
To prove my hypothesis, I deconstructed my concept down to a
simple question: Could government workforce data be
exploited on a grand scale? To answer this question, I first
needed to analyze the existing datasets available on Data.Gov
using an existing framework. For analyzing my techniques, I
selected the MITRE Adversarial Tactics, Techniques, and
Common Knowledge (ATT&CK) Framework. ATT&CK
has already been adopted for Structured Threat Information
Expression (STIX) and Trusted Automated Exchange of
Intelligence Information (TAXII) to support exploitation
research. The research conducted on Data.Gov datasets
will focus on only four adversarial techniques, all of which are
part of Tactic TA0043, Reconnaissance. When combined,
these techniques enable highly accurate targeting of the U.S.G.
Precursory research of the Chicago dataset showed that the
following techniques could be directly achieved through
Data.Gov:

* Technique 1589.003 - Employee Names
* Technique 1591.001 –Physical Locations
* Technique 1591.004 – Identify Roles

Using just these key data points, the following research will
show that additional techniques can be achieved through
inference, open-source databases, and common vulnerabilities
& exposures (CVE).

# 4. Research
Research towards the hypothesis began on Data.Gov. The
OPEN Government Act mandated the creation of an
Application Programming Interface or API so that users could
interact with the catalogue in a variety of applications. The API
for Data.Gov was created by General Service Administration's
18F Team, which manages their "/Developer" Program. In
the interest of openness, Data.Gov uses a JSON metadata
schema. This API structure allows users to parse data using
widely available JSON libraries, which are available in popular
high-level interpreter languages, like R and Python. This
research used Python3 since it currently represents the latest
iteration of the most popular scripting language in the United
States.

```json
{
  "help" : "https://catalog.data.gov/api/3/action/help_show?name=group_list",
  "success": true,
  "result": [
    "agriculture8571",
    "climate5434",
    "energy9485",
    "local",
    "maritime",
    "ocean9585",
    "older-adults-health-data"
  ]
}
```
Script 1 - Data.Gov API response for a Group List request:
https://catalog.data.gov/api/3/action/group_list

Using the publishers discovered in the Data.Gov catalogue, I
conducted research into each organization to determine
correlations between real-world events (e.g., inference, doxing,
phishing, attrition, or influence) and their publication of data.
Research into each organization was limited to sources found
using the Google, DuckDuckGo, and Yahoo! search engines.

# 5. Assessment
After concluding research, I established a chain of scripts that
needed to be generated to assess the risks. The first script,
called GovDataCollector, would interact with the Data.Gov
API to mass-download datasets. The second script,
GovDataInferrer, would ingest most datasets, infer usernames
and e-mail addresses, and propose an attack type based solely
on income. The final script, GovDataValidator, would test the
e-mail addresses against mail exchange servers using either
Simple Mail Transfer Protocol (SMTP) or an Office365
vulnerability.

# 6. Analysis
As part of the analysis phase, I established six measures of
performance and effectiveness: three for inference and three for
a whaling campaign. Unfortunately, I was unable to partner
with a local government organization to conduct a whaling
campaign as part of the assessment. As a result, this section
will only focus on the inference metrics and policy
considerations that have come to light through research.

# 7. Findings and Recommendations
Before the OPEN Government Act, the identities of most
government employees would have been protected by existing
layers of government process like supervisors or the Freedom
of Information Act. Even in an academic setting, data is only
openly provided to a specific person for a specific activity with
a pre-defined goal in mind. In the case of data.gov, none of this
information is collected when a user accesses data related to
government employee names. Existing restrictions are focused
on denying access to sensitive information. To the U.S.
government, public anonymous access to workforce data is not
a vulnerability – "it is a feature."
