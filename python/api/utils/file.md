# HƯỚNG PHÁT TRIỂN XỬ LÝ FILE TEMP

1. Khi hệ thống cần hiệu năng cao hoặc xử lý nhiều request,
   bạn nên chuyển sang trả ảnh bằng raw bytes:
       _, buf = cv2.imencode(".png", result)
       return Response(buf.tobytes(), media_type="image/png")

2. Khi triển khai trên Docker / serverless (Cloud Run, AWS Lambda):
   Một số môi trường không cho ghi file → cách trả bytes là tối ưu.

3. Có thể cho phép client lựa chọn:
   - trả file PNG
   - trả base64
   - trả direct binary stream

4. Thư mục temp có thể chuyển thành thư mục hệ thống:
       tempfile.gettempdir()

5. Có thể thêm cron job dọn dẹp tự động (nếu bạn muốn giữ file lâu hơn).
