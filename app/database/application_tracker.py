from datetime import datetime

from app.database.database import get_connection



class ApplicationTracker:



    def save_job(
        self,
        job
    ):

        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            INSERT INTO applications
            (
                title,
                company,
                url,
                status,
                created
            )

            VALUES (?, ?, ?, ?, ?)

            """,

            (

                job.get(
                    "title",
                    ""
                ),

                job.get(
                    "company",
                    ""
                ),

                job.get(
                    "url",
                    ""
                ),

                "Saved",

                datetime.now().strftime(
                    "%Y-%m-%d"
                )

            )

        )


        conn.commit()

        conn.close()



    def update_status(
        self,
        title,
        status
    ):


        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE applications

            SET status = ?

            WHERE title = ?

            """,

            (

                status,

                title

            )

        )


        conn.commit()

        conn.close()



    def get_all(self):

        conn = get_connection()

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT *
            FROM applications
            ORDER BY id DESC
            """
        )


        results = cursor.fetchall()


        conn.close()


        return results