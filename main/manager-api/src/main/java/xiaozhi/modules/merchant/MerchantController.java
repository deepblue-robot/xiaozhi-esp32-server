package xiaozhi.modules.merchant;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.page.PageData;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.merchant.dto.MerchantBindAgentRequest;
import xiaozhi.modules.security.user.SecurityUser;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

@Tag(name = "商户管理")
@RestController
@RequestMapping("merchant")
public class MerchantController {


    @Autowired
    private MerchantService merchantService;

    @GetMapping("/all")
    @Operation(summary = "商户列表")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "当前页码，从1开始", required = true),
            @Parameter(name = Constant.LIMIT, description = "每页显示记录数", required = true),
    })
    public Result<PageData<MerchantEntity>> list(@Parameter(hidden = true) @RequestParam Map<String, Object> params){
        PageData<MerchantEntity> page = merchantService.merchantPage(params);
        return new Result<PageData<MerchantEntity>>().ok(page);
    }


    @Autowired
    private MerchantAgentService merchantAgentService;

    @PostMapping("/bindAgent")
    @Operation(summary = "绑定智能体")
    public Result<Boolean> bindAgent(@RequestBody MerchantBindAgentRequest merchantBindAgentRequest){
        UserDetail user = SecurityUser.getUser();
        List<MerchantAgentEntity> merchantAgentEntities = new ArrayList<>();
        List<String> agentIds = merchantBindAgentRequest.getAgentIds();
        Long merchantId = merchantBindAgentRequest.getMerchantId();
        for(int i = 0;i < agentIds.size(); i++){
            MerchantAgentEntity merchantAgentEntity = new MerchantAgentEntity();
            merchantAgentEntity.setMerchantId(merchantId);
            merchantAgentEntity.setAgentId(agentIds.get(i));
            merchantAgentEntity.setCreateDate(new Date());
            merchantAgentEntity.setCreator(user.getId());
            merchantAgentEntities.add(merchantAgentEntity);
        }
        Boolean result = merchantAgentService.insertBatch(merchantAgentEntities);
        return new Result<Boolean>().ok(result);
    }


    @GetMapping("/queryMerchantAgentList/{merchantId}")
    @Operation(summary = "查询商户绑定的智能体")
    public Result<List<MerchantAgentEntity>> queryMerchantAgentList(@PathVariable Long merchantId){
        List<MerchantAgentEntity> list = merchantAgentService.getMerchantAgentList(merchantId);
        return new Result<List<MerchantAgentEntity>>().ok(list);
    }

}
