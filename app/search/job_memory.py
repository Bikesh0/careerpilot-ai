from app.database.database import get_connection



class JobMemory:



    def is_seen(
        self,
        title,
        company
    ):

        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT id

            FROM jobs

            WHERE title = ?

            AND company = ?

            """,

            (
                title,
                company
            )

        )


        result = cursor.fetchone()


        conn.close()


        return result is not None




    def filter_new_jobs(
        self,
        jobs
    ):

        new_jobs = []


        for job in jobs:


            if not self.is_seen(

                job.get(
                    "title",
                    ""
                ),

                job.get(
                    "company",
                    ""
                )

            ):

                new_jobs.append(
                    job
                )


        return new_jobs
    