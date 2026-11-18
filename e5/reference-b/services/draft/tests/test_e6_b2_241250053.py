import unittest

from draft.autobuild import prepare_candidate


BASE = (
    "FROM python:3.13-slim\n"
    "WORKDIR /work\n"
    "COPY main.c Makefile ./\n"
    "RUN make\n"
    'CMD ["./hello"]\n'
)
PINNED_FROM = "FROM python:3.13-slim@sha256:" + "a" * 64
CANDIDATE = BASE.replace("FROM python:3.13-slim", PINNED_FROM).replace(
    "RUN make",
    "RUN apt-get update && apt-get install -y build-essential\nRUN make",
)


class B2E6CandidateBoundaryTests(unittest.TestCase):
    def test_multistage_candidate_is_rejected_before_build(self):
        multistage = CANDIDATE.replace(
            "WORKDIR /work",
            PINNED_FROM + "\nWORKDIR /work",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Only single-stage candidates are supported",
        ):
            prepare_candidate(BASE, multistage)


if __name__ == "__main__":
    unittest.main()
