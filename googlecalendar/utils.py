import datetime
def get_free_slots(busy_times,free_slots,current,end_datetime,tz):
        
        for slot in busy_times:
                busy_start = datetime.datetime.fromisoformat(slot['start']).astimezone(tz)
                busy_end = datetime.datetime.fromisoformat(slot['end']).astimezone(tz)

                if current < busy_start:
                    free_slots.append({
                        "start": current.isoformat(),
                        "end": busy_start.isoformat()
                    })
                current = max(current, busy_end)

        if current < end_datetime:
            free_slots.append({
                "start": current.isoformat(),
                "end": end_datetime.isoformat()
            })
                
