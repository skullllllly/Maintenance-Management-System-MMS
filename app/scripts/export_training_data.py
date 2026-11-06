import asyncio
import csv
import json
from pathlib import Path 

from sqlalchemy import select

from app.db.session import async_session
from app.models.ticket_image import TicketImage

OUTPUT_PATH=Path("training_data.csv")
LIMIT=100_000

async def export_training_data()->None:
    async with async_session() as db:

        stmt=(
            select(
            TicketImage.image_id,
            TicketImage.cnn_features,
            TicketImage.defect_label,
        )
        .where(TicketImage.cnn_features.is_not(None))
        .where(TicketImage.processing_status == "COMPLETED")
        .where(TicketImage.defect_label.is_not(None))
        .order_by(TicketImage.image_id.asc())
        .limit(LIMIT)

        )

        rows=(await db.execute(stmt)).all()

    valid_rows=[
        row 
        for row in rows
        if isinstance(row.cnn_features,list)
        and len(row.cnn_features) == 2048
        and row.defect_label is not None 
        and row.defect_label.strip()
        
        ]

    with OUTPUT_PATH.open("w",newline="",encoding="utf-8") as output:
        writer= csv.writer(output)
        writer.writerow(["image_id","label","cnn_features"])
        for row in valid_rows:
            writer.writerow([
                row.image_id,
                row.defect_label.strip(),
                json.dumps(row.cnn_features,separators=(",",":")),

            ])

    print(f"Exported {len(valid_rows)}  trsining rows to {OUTPUT_PATH}")

if __name__ =="__main__":
    asyncio.run(export_training_data())