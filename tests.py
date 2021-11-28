




# from log_management.models import MaliciousIPSearchLog
import datetime
import json
import time

import requests
from django.db.models import F
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.views import APIView

from api.middleware import api
from common.public import PAGENUM, PAGE, check_device_params
from common.utils import get_show_field, get_uuid
from device_management.device import add_device, list_data, search, get_one, edit, remove, update_status, \
    get_device_basic
from device_management.models import Device
from device_management.serializers import DeviceSerializer
from log_management.log import add_opration
from log_management.models import MaliciousIPSearchLog
from system_management.models import DeviceBasic
from api.middleware import api
from common.public import get_login_username

# Create your views here.
class DeviceView(APIView):

    @staticmethod
    def get(request):
        """
        设备列表（搜索/分页）
        :param request:
        :return:
        """
        request_query = request.query_params
        page = request_query.get("page", PAGE)
        page_num = request_query.get("pageNum", PAGENUM)
        search_params = request_query.get("params", None)

        try:
            if not search_params:
                data, totals = list_data(page, page_num)
            else:
                data, totals = search(page, page_num, search_params)

            data_ser = DeviceSerializer(data, many=True)

            return Response({"code": 200, "message": "获取成功", "totals": totals, "data": data_ser.data})
        except Exception as e:
            return Response({"code": 500, "message": str(e), "data": [], "totals": []})

    @staticmethod
    def post(request):
        """
        设备添加
        :param request:
        :return:
        """
        current_user = get_login_username()
        request_query = request.body
        if not request_query:
            return Response({"code": 500, "message": "参数不能为空"})
        params = json.loads(request_query)
        # 参数校验
        params, msg = check_device_params(params)
        if msg != "":
            return Response({"code": 500, "message": msg})

        try:
            result = add_device(params)
            add_opration({"uname": "Q", "business": "移动", "module": "设备管理", "function": "新增",
                          "description": "用户{}新增设备:{}".format(current_user, params["name"]), "result": 1})
            return Response(result)
        except Exception as e:
            add_opration({"uname": "Q", "business": "移动", "module": "设备管理", "function": "新增",
                          "description": "用户{}新增设备:{}".format(current_user, params["name"]), "result": 0})
            return Response({"code": 500, "message": str(e), "data": [], "totals": []})

    def options(self, request, *args, **kwargs):
        """
        工具详情
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        request_query = request.body
        if not request_query:
            return Response({"code": 404, "message": "参数不能为空"})
        request_json = json.loads(request_query)
        devid = request_json["devid"]
        if not devid:
            return Response({"code": 404, "message": "请选择要查看的工具"})

        try:
            # devid = int(devid)
            data = get_one(devid)
            if not data:
                return Response({"code": 404, "message": "您要找的工具不存在"})

            data_ser = DeviceSerializer(data, many=True)
            return Response({"code": 200, "message": "获取成功", "totals": 1, "data": data_ser.data})
        except Exception as e:
            return Response({"code": 500, "message": str(e), "totals": [], "data": []})

    @staticmethod
    def delete(request):
        """
        设备删除
        :param request:
        :return:
        """
        current_user = "test_user"
        request_query = request.body
        if not request_query:
            return Response({"code": 500, "message": "参数不能为空"})
        request_params = json.loads(request_query)
        devid = request_params["devid"]
        if not devid:
            return Response({"code": 500, "message": "请选择要删除的数据！"})
        device_data = Device.objects.filter(devid=devid)
        if not device_data:
            return Response({"code": 500, "message": "您要删除的工具不存在！"})
        name = device_data.get().name
        try:

            remove(devid)
            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "删除",
                          "description": "用户{}删除工具:{}".format(current_user, name), "result": 1})

            return Response({"code": 200, "message": "删除成功", "totals": [], "data": []})
        except Exception as e:
            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "删除",
                          "description": "用户{}删除工具:{}".format(current_user, name), "result": 0})
            return Response({"code": 500, "message": str(e)})

    @staticmethod
    def put(request):
        """
        工具编辑
        :param request:
        :return:
        """
        current_user = "test_user"
        request_query = request.body
        if not request_query:
            return Response({"code": 500, "message": "参数不能为空"})
        request_params = json.loads(request_query)
        devid = request_params["devid"]
        if not devid:
            return Response({"code": 500, "message": "请选择要编辑得数据"})

        # devid = int(devid)
        device_data = Device.objects.filter(devid=devid)
        if not device_data:
            return Response({"code": 500, "message": "您要删除的工具不存在"})
        old_name = device_data.get().name
        # from django.http import HttpResponse
        try:

            params, msg = check_device_params(request_params)
            if msg != "":
                return Response({"code": 500, "message": msg, "totals": [], "data": []})
            # params = request_params
            params.pop("devid")

            desc = edit(devid, params)
            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "编辑",
                          "description": "用户{}编辑工具:{}{}".format(current_user, old_name, desc), "result": 1})

            return Response({"code": 200, "message": "修改成功！", "data": [], "totals": []})

        except Exception as e:
            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "编辑",
                          "description": "用户{}编辑工具:{}".format(current_user, old_name), "result": 0})

            return Response({"code": 500, "message": str(e), "data": [], "totals": []})
# 工具类型三联动数据获取
class DeviceBasicView(APIView):

    @staticmethod
    def get(request):
        """

        :return:
        """
        try:
            from django.http import HttpResponse
            data = get_device_basic()
            return Response({"code": 200, "message": "查询成功", "data": data})
        except Exception as e:
            raise e
class DeviceStatusView(APIView):

    @staticmethod
    def put(request):
        """
        设备信息上报
        :param request:
        :return:
        """
        current_user = "test_user"
        request_query = request.body
        if not request_query:
            return Response({"code": 404, "message": "参数错误"})
        params = json.loads(request_query)
        if not params["devid"]:
            return Response({"code": 500, "message": "请选择工具"})
        devid = params["devid"]
        device = Device.objects.filter(devid=devid)
        if not device:
            return Response({"code": 404, "message": "工具不存在"})
        # collect_logger = logging.getLogger("collect")

        try:

            if device.get().status in [0, 2]:
                params["online_time"] = int(time.time())
            runinfo = params["runinfo"]
            params["cpu"] = runinfo["cpu"]
            params["mem"] = runinfo["mem"]
            params["dist"] = runinfo["disk"]
            result = update_status(params)

            # collect_logger.info("requestParams:{}".format(request_query))

            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "工具信息上报",
                          "description": "用户{}上报工具信息:{}".format(current_user, device.get().name), "result": 1})

            return Response(result)

        except Exception as e:
            # collect_logger.info("requestParams:{}".format(request_query))

            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "工具信息上报",
                          "description": "用户{}上报工具信息:{}".format(current_user, device.get().name), "result": 0})

            return Response({"code": 500, "message": str(e), "data": [], "totals": []})
class DeviceOffStatusView(APIView):

    @staticmethod
    def put(request):
        current_user = "test_user"
        request_query = request.body
        if not request_query:
            return Response({"code": 404, "message": "参数错误"})
        # collect_logger = logging.getLogger("collect")
        params = json.loads(request_query)
        devid = params["devid"]
        device = Device.objects.filter(devid=devid)
        if not device:
            return Response({"code": 404, "message": "工具不存在"})
        try:

            if device.get().status == 2:
                return Response({"code": 500, "message": "请先激活工具"})
            device.update(status=0)
            # collect_logger.info("requestParams:{}".format(request_query))

            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "工具信息上报",
                          "description": "用户{}离线工具:{}".format(current_user, device.get().name), "result": 1})
            return Response({"code": 200, "message": "工具已离线！", "data": [], "totals": []})

        except Exception as e:
            # collect_logger.info("requestParams:{}".format(request_query))

            add_opration({"uname": current_user, "business": "移动", "module": "工具管理", "function": "工具信息上报",
                          "description": "用户{}离线工具:{}".format(current_user, device.get().name), "result": 0})

            return Response({"code": 500, "message": str(e), "data": [], "totals": []})
class MaliciousAddressCheckView(APIView):

    @staticmethod
    def put(request):
        """
        恶意网址查询
        :param request:
        :return:
        """
        conn = get_redis_connection()
        request_url = "http://127.0.0.1:4434/device_management/callapi/domaindetect"
        request_query = request.body
        request_params = json.loads(request_query)
        nums = len(request_params)
        if nums > 10:
            return Response({"code": 500, "message": "一次仅限查询十条", })
        request_deivce_data = request_params["device"]
        for device_data in request_deivce_data:
            device = Device.objects.filter(devid=device_data["devid"]).get()
            # 更新数据库
            today = int(time.mktime(time.strptime(str(datetime.date.today()), '%Y-%m-%d')))
            malicious_log = MaliciousIPSearchLog.objects.filter(devid=device_data["devid"]).filter(search_time=today)
            if malicious_log:
                malicious_log.update(count=F("count") + 1)
            else:
                params = dict()
                params["search_time"] = today
                params["devid"] = device_data["devid"]
                params["device_name"] = device.device_name
                params["business"] = device.business
                params["owner"] = device.department
                params["count"] = 1
                MaliciousIPSearchLog.objects.create(**params)

            # 更新redis
            redis_res = conn.get(device_data["url"])
            result_data = list()
            if redis_res:
                data = dict()
                data["devid"] = device_data["devid"]
                data["url"] = device_data["url"]
                data["is_malicious"] = redis_res["is_malicious"]
                data["judgments"] = redis_res["judgments"]
                # result_data.append(data)
            else:
                data = dict()
                data["devid"] = device_data["devid"]
                data["url"] = device_data["url"]
                param = {"domain": device_data["url"]}
                request_res = requests.post(request_url, data=param)
                request_json = json.loads(request_res.json())
                if request_json["result_code"] != 200:
                    return Response({"code": request_json["result_code"], "data": "查询失败"})
                data["is_malicious"] = request_json["is_malicious"]
                data["judgments"] = request_json["judgments"]
                conn.set(device["url"], result_data)
            result_data.append(data)

        return Response({"code": 200, "message": "查询成功", "data": result_data})
from common.utils import get_show_field
from django.http import HttpResponse
class FieldShowView(APIView):

    @staticmethod
    def get(request):
        """
        工具列表抬头字段展示
        :param request:
        :return:
        """
        current_user = "hanlu"
        conn = get_redis_connection()
        redis_res = conn.get(current_user)

        if not redis_res:
            show_field = get_show_field()
            # show_field = json.dumps(show_field)
            conn.set(current_user,show_field)
        else:
            show_field = redis_res
        # return HttpResponse(show_field)
        # show_field = json.loads(show_field)
        return Response({"code": 200, "message": "获取成功", "data": show_field})

    @staticmethod
    def post(request):
        current_user = "hanlu"
        request_json = request.body
        # request_params = json.loads(request_json)
        conn = get_redis_connection()
        conn.set(current_user,request_json)
        return Response({"code": 200, "message": "配置成功", "data": []})
class DepartmentView(APIView):
    @staticmethod
    def get(request):
        device_data = Device.objects.exclude(department="").values("department").order_by("department").distinct()
        result = list()
        for i in device_data:
            value = dict()
            value["value"] = i["department"]
            result.append(value)
        return Response({"code": 200, "message": "successful", "data": result})
class VendorsView(APIView):
    @staticmethod
    def get(request):
        vendors = DeviceBasic.objects.values("vendor").order_by("vendor").distinct()
        result = list()
        for i in vendors:
            value = dict()
            value["value"] = i["vendor"]
            result.append(value)
        return Response({"code": 200, "message": "successful", "data": result})

#前端响应后端向middleware发送请求（接口）
class DeviceIPPolicyView(APIView):

    @staticmethod
    def get(request):
        devid = request.GET.get("devid", None)
        print("devid:", devid)
        try:
            resp = api.get_ip_policy(devid)
            print(resp.text)
            print(resp.status_code)
            if resp.status_code != 200:
                return Response({"code":resp.status_code, "data": "获取设备IP策略请求失败"})

            return Response({"code": 200, "message": "获取设备IP策略请求成功", "data": ""})

        except Exception as e:
            return Response({"code": 500, "message": str(e), "data": []})

    @staticmethod
    def put(request):
        """
        工具=》IP过滤策略=》修改=》下发
        :param request:
        :return:
        """
        # 前端参数
        web_query = request.body
        print('web_query: ', web_query)
        if not web_query:
            return Response({"code": 500, "message": "参数错误", "data": []})
        web_json = json.loads(web_query)
        print('web_query2: ', web_query)
        # 请求中间件参数
        # middware_url = "localhost:2232"
        middware_params = dict()
        middware_params["devid"] = web_json["devid"]
        middware_params["cmdseq"] =str(get_uuid())
        middware_params["switch"] = web_json["switch"]
        middware_params["iplists"] = list()

        for ip in web_json["iplists"]:
            iplistPub = dict()
            iplistPub["type"] = "ipv4"
            iplistPub["protocol"] = ["ANY"]
            iplistPub["srcip"] = "ANY"
            iplistPub["srcport"] = "ANY"
            iplistPub["destport"] = "ANY"
            iplistPub["destip"] = ip
        middware_params["iplists"].append(iplistPub)


        try:
            # request_res = requests.post(middware_url, middware_params)
            request_res = api.config_ip_policy(middware_params)
            print('request_res: ', request_res)
            print('request_res.status_code: ', request_res.status_code)
            if request_res.status_code != 200:
                return Response({"code": 500, "message": "下发失败", "data": []})
            return Response({"code": 200, "message": "下发成功", "data": request_res})
        except Exception as e:
            return Response({"code": 500, "message": str(e), "data": []})


# 从中间件获取的IP数据返给前端
class DeviceIPViews(APIView):

    @staticmethod
    def get(request):
        """
        工具=》IP过滤策略
        :param request:
        :return:
        """
        devid = request.GET.get("devid", None)
        print("devid:Deviceipview:",devid)
        if not devid:
            return Response({"code": 500, "message": "请选择要配置的工具", "data": []})
        try:

            conn = get_redis_connection()
            redis_res = conn.get(devid)
            if  not redis_res:

                return Response({"code": 404, "message": "中间件未传数据", "data": []})
            redis_res = json.loads(redis_res)
            start_time = conn.get('start_time')

            print('str_time: ',start_time)
            nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            end_time = time.mktime(time.strptime(str(nowtime), '%Y-%m-%d %H:%M:%S'))
            if start_time:
                start_time = start_time.decode()
                start_time = time.mktime(time.strptime(str(start_time), '%Y-%m-%d %H:%M:%S'))
                if end_time - start_time > 65:
                    conn.delete(devid)
                    return Response({"code": 404, "message": "请求已超时", "data":[]})
            if not redis_res:
                return Response({"code": 500, "message": "该设备策略信息未上报完成", "data": redis_res})

            return Response({"code": 200, "message": "查询成功", "data": redis_res})
        except Exception as e:
            return Response({"code": 500, "message": str(e), "data": []})

# 中间件通过put请求传数据存入缓存redis中
class MiddlewareIPView(APIView):

    @staticmethod
    def put(request):

        """
        中间件上报工具策略信息
        :param request:
        :return:
        """
        request_json = request.body
        if not request_json:
            return Response({"code": 500, "message": "参数错误！", "data": []})

        request_params = json.loads(request_json)
        print('request_params:',request_params)
        devid = request_params["devid"]
        try:
            conn = get_redis_connection()
            # 组装redis数据
            redis_data = dict()
            redis_data["switch"] = request_params["switch"]
            iplist = list()
            for ip in request_params["iplists"]:
                iplist.append(ip["destip"])
            redis_data["iplists"] = iplist
            redis_data['devid'] = devid
            res = conn.set(devid, redis_data)  #{'switch': 0, 'iplists': ['192.168.8.1-192.168.8.100', '192.168.255.255']}
            start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # start_time = json.dumps(start_time)
            start_time = conn.set('start_time', start_time)
            print('start_time: ', start_time)

            return Response({"code": 200, "message": "查询成功", "data": res})

        except Exception as e:
            return Response({"code": 500, "message": str(e), "data": []})

##################设备域名策略配置##################
# 前端向后台发送的设备域名策略请求，包括发送指令和下发
class DeviceDomainPolicyView(APIView):

    @staticmethod
    def get(request):
        request_query = request.query_params
        devid = request_query.get("devid")
        if not devid:
            return Response({"code": 500, "data": "请指定设备ID"})
        conn = get_redis_connection()
        key = get_device_domain_policy_key_for_catch(devid)
        domain_policy = conn.get(key)
        if domain_policy:
            conn.delete(key)
        try:
            resp = api.get_domain_policy(devid)
            print('request_res: ', resp)
            print('request_res.status_code: ', resp.status_code)
            if resp.status_code != 200:
                return Response({"code":resp.status_code  , "data": "获取设备域名策略请求失败"})

            return Response({"code": 200, "message": "获取设备域名策略请求成功", "data": ""})
        except Exception as e:
            return Response({"code": 500, "message": str(e), "data": []})

    @staticmethod
    def put(request):
        conf = json.loads(request.body)
        conf["cmdseq"] = str(get_uuid())
        resp = api.config_domain_policy(conf)
        if resp.status_code != 200:
            return Response({"code": resp.status_code, "data": "设备域名策略下发失败"})

        return Response({"code": 200, "message": "设备域名策略下发成功", "data": ""})

# 前端异步查询域名策略
class DeviceDomainPolicyResultView(APIView):
    @staticmethod
    def get(request):
        request_query = request.query_params
        devid = request_query.get("devid")
        if not devid:
            return Response({"code": 500, "data": "请指定设备ID"})
        key = get_device_domain_policy_key_for_catch(devid)

        conn = get_redis_connection()
        domain_policy = conn.get(key)
        if not domain_policy:
            return Response({"code": 500, "message": "中间件还未返回设备域名策略", "data": ""})

        conn.delete(key)
        return Response({"code": 200, "message": "获取设备域名策略请求成功", "data": domain_policy})

def get_device_domain_policy_key_for_catch(devid):
    return devid + "domain"

# 中间件上报设备域名策略配置
class MidwareDomainResultView(APIView):
    @staticmethod
    def put(request):
        domain_policy = request.body
        print("request_query:", domain_policy)
        domain_policy_json = json.loads(domain_policy)
        print("request_params:", domain_policy_json)
        if not domain_policy_json:
            return Response({"code": 500, "message": "no data"})

        conn = get_redis_connection()
        key = get_device_domain_policy_key_for_catch(domain_policy_json["devid"])
        conn.set(key, domain_policy_json)
        return Response({"code": 200, "message": "successful"})
##################设备域名策略配置##################







