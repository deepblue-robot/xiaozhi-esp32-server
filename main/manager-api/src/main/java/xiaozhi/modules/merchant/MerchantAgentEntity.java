package xiaozhi.modules.merchant;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.EqualsAndHashCode;

import java.util.Date;

/**
 * 表名：ai_merchant_agent
 * 表注释：商户智能体关联表
*/
@EqualsAndHashCode(callSuper = false)
@TableName("ai_merchant_agent")
@Schema(description = "商户关联智能体信息")
public class MerchantAgentEntity {
    /**
     * id
     */
    @TableId(type = IdType.AUTO)
    @Schema(description = "ID")
    private Long id;

    /**
     * 商户ID
     */
    @TableField(value = "merchant_id")
    private Long merchantId;

    /**
     * 智能体ID
     */
    @TableField(value = "agent_id")
    private String agentId;

    /**
     * 创建时间
     */
    @TableField(value = "create_date")
    private Date createDate;

    /**
     * 创建者
     */
    private Long creator;

    /**
     * 获取id
     *
     * @return id - id
     */
    public Long getId() {
        return id;
    }

    /**
     * 设置id
     *
     * @param id id
     */
    public void setId(Long id) {
        this.id = id;
    }

    /**
     * 获取商户ID
     *
     * @return merchantId - 商户ID
     */
    public Long getMerchantId() {
        return merchantId;
    }

    /**
     * 设置商户ID
     *
     * @param merchantId 商户ID
     */
    public void setMerchantId(Long merchantId) {
        this.merchantId = merchantId;
    }

    /**
     * 获取智能体ID
     *
     * @return agentId - 智能体ID
     */
    public String getAgentId() {
        return agentId;
    }

    /**
     * 设置智能体ID
     *
     * @param agentId 智能体ID
     */
    public void setAgentId(String agentId) {
        this.agentId = agentId;
    }

    /**
     * 获取创建时间
     *
     * @return createDate - 创建时间
     */
    public Date getCreateDate() {
        return createDate;
    }

    /**
     * 设置创建时间
     *
     * @param createDate 创建时间
     */
    public void setCreateDate(Date createDate) {
        this.createDate = createDate;
    }

    /**
     * 获取创建者
     *
     * @return creator - 创建者
     */
    public Long getCreator() {
        return creator;
    }

    /**
     * 设置创建者
     *
     * @param creator 创建者
     */
    public void setCreator(Long creator) {
        this.creator = creator;
    }
}