package xiaozhi.modules.merchant;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;

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



}
